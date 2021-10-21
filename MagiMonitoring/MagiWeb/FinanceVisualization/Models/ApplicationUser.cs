using Microsoft.AspNetCore.Identity;

namespace FinanceVisualization.Models
{
    public class ApplicationUser : IdentityUser
    {
        public SubscriptionEnum SubscriptionEnum { get; set; }

        public bool CanAddNews { get; set; }
    }
}
