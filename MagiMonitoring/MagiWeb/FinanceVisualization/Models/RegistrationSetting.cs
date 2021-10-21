using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class RegistrationSetting
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public bool Status { get; set; }
    }
}
