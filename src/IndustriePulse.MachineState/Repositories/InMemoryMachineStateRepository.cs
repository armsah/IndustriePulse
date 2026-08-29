using System.Collections.Concurrent;
using IndustriePulse.MachineState.Models;

namespace IndustriePulse.MachineState.Repositories;

public sealed class InMemoryMachineStateRepository : IMachineStateRepository
{
    private readonly ConcurrentDictionary<string, MachineCurrentState> _states = new();

    public Task<MachineCurrentState?> GetAsync(
        string machineId,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        _states.TryGetValue(machineId, out var state);

        return Task.FromResult(state);
    }

    public Task<bool> TryAdvanceAsync(
        MachineCurrentState candidate,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        while (true)
        {
            if (!_states.TryGetValue(candidate.MachineId, out var existing))
            {
                if (_states.TryAdd(candidate.MachineId, candidate))
                {
                    return Task.FromResult(true);
                }


                continue;
            }

            if (candidate.Sequence <= existing.Sequence)
            {
                return Task.FromResult(false);
            }

            if (_states.TryUpdate(candidate.MachineId, candidate, existing))
            {
                return Task.FromResult(true);
            }
        }
    }
}
