using IndustriePulse.MachineState.Models;

namespace IndustriePulse.MachineState.Repositories;

public interface IMachineStateRepository
{
    Task<MachineCurrentState?> GetAsync(
        string machineId,
        CancellationToken cancellationToken = default);

    Task<bool> TryAdvanceAsync(
        MachineCurrentState candidate,
        CancellationToken cancellationToken = default);
}
