using FinanceVisualization.Models;
using IdentityServer4.EntityFramework.Options;
using Microsoft.AspNetCore.ApiAuthorization.IdentityServer;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;

namespace FinanceVisualization.Data
{
    public class ApplicationDbContext : ApiAuthorizationDbContext<ApplicationUser>
    {
        public DbSet<Event> Events { get; set; }

        public DbSet<EventPredictor> EventPredictors { get; set; }

        public DbSet<IndicatorDetail> IndicatorDetails { get; set; }

        public DbSet<UserSymbolGroup> UserSymbolGroups { get; set; }

        public DbSet<UserSymbolGroupDetail> UserSymbolGroupDetails { get; set; }

        public DbSet<FinancialStatus> FinancialStatuses { get; set; }

        public DbSet<Correlation> Correlations { get; set; }

        public DbSet<Feedback> Feedbacks { get; set; }

        public DbSet<ManualNews> ManualNews { get; set; }

        public DbSet<RegistrationSetting> RegistrationSettings { get; set; }

        public ApplicationDbContext(
            DbContextOptions options,
            IOptions<OperationalStoreOptions> operationalStoreOptions) : base(options, operationalStoreOptions)
        {
        }
    }
}
