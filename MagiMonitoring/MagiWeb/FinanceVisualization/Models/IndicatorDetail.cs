using FinanceVisualization.Helpers;
using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class IndicatorDetail
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public string Symbol { get; set; }

        public float Volume { get; set; }

        public float Price { get; set; }

        public string EventRole { get; set; }

        public int EventId { get; set; }

        public Event Event { get; set; }

        [NotMapped]
        public FirmInfo FirmInfo { get; set; }
    }
}
