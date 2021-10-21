using System;
using System.Linq;

namespace FinanceVisualization.Helpers
{
    public static class RegistrationHelper
    {
        private static string[] authenticatedEmails = new string[] {
            "ozkankilic@gmail.com",
            "hmlatapie@gmail.com",
            "samety06@gmail.com"
            //"sametdumankaya@gmail.com"
        };

        public static bool IsAuthenticatedForChangingRegistration(string email)
        {
            return authenticatedEmails.Contains(email.Trim());
        }
    }
}
