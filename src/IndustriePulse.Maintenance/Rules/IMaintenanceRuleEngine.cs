using IndustriePulse.Maintenance.Contracts;

namespace IndustriePulse.Maintenance.Rules;

public interface IMaintenanceRuleEngine
{
    IReadOnlyList<MaintenanceCommand> Evaluate(MaintenanceRuleInput input);
}
