using Microsoft.AspNetCore.Identity.UI.Services;
using SendGrid;
using SendGrid.Helpers.Mail;
using System.Threading.Tasks;

namespace FinanceVisualization.Services
{
    public class EmailSender : IEmailSender
    {
        public async Task SendEmailAsync(string email, string subject, string htmlMessage)
        {
            var apiKey = "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";
            var client = new SendGridClient(apiKey);
            var from = new EmailAddress("ff088210.magifinance.onmicrosoft.com@amer.teams.ms");
            var to = new EmailAddress(email);
            var msg = MailHelper.CreateSingleEmail(from, to, subject, "", htmlMessage);
            await client.SendEmailAsync(msg);
        }
    }
}
