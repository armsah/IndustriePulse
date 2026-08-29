using System.Net;
using IndustriePulse.MachineState.Models;
using Microsoft.Azure.Cosmos;

namespace IndustriePulse.MachineState.Repositories;

public sealed class CosmosMachineStateRepository : IMachineStateRepository
{
    private readonly Container _container;

    public CosmosMachineStateRepository(Container container)
    {
        _container = container;
    }

    public async Task<MachineCurrentState?> GetAsync(
        string machineId,
        CancellationToken cancellationToken = default)
    {
        try
        {
            var response = await _container.ReadItemAsync<MachineCurrentState>(
                machineId,
                new PartitionKey(machineId),
                cancellationToken: cancellationToken);

            return response.Resource;
        }
        catch (CosmosException notFoundException)
            when (notFoundException.StatusCode == HttpStatusCode.NotFound)
        {
            return null;
        }
    }

    public async Task<bool> TryAdvanceAsync(
        MachineCurrentState candidate,
        CancellationToken cancellationToken = default)
    {
        while (true)
        {
            cancellationToken.ThrowIfCancellationRequested();

            MachineCurrentState? existing;

            try
            {
                var response = await _container.ReadItemAsync<MachineCurrentState>(
                    candidate.MachineId,
                    new PartitionKey(candidate.MachineId),
                    cancellationToken: cancellationToken);

                existing = response.Resource;
            }
            catch (CosmosException notFoundException)
                when (notFoundException.StatusCode == HttpStatusCode.NotFound)
            {
                try
                {
                    await _container.CreateItemAsync(
                        candidate,
                        new PartitionKey(candidate.MachineId),
                        cancellationToken: cancellationToken);

                    return true;
                }
                catch (CosmosException conflictException)
                    when (conflictException.StatusCode == HttpStatusCode.Conflict)
                {
                    continue;
                }
            }

            if (candidate.Sequence <= existing.Sequence)
            {
                return false;
            }

            try
            {
                await _container.ReplaceItemAsync(
                    candidate,
                    candidate.MachineId,
                    new PartitionKey(candidate.MachineId),
                    new ItemRequestOptions
                    {
                        IfMatchEtag = existing.ETag
                    },
                    cancellationToken);

                return true;
            }
            catch (CosmosException preconditionException)
                when (preconditionException.StatusCode == HttpStatusCode.PreconditionFailed)
            {
                // Another writer advanced this machine between our read and replace.
                // Re-read and compare sequence numbers again.
            }
        }
    }
}
