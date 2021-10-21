using FinanceVisualization.Helpers;
using System;
using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class EventPredictor
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public string Symbol { get; set; }

        public float PredictivePower { get; set; }

        public DateTime? TimeStamp { get; set; }

        public int EventId { get; set; }

        public Event Event { get; set; }

        [NotMapped]
        public FirmInfo FirmInfo { get; set; }
    }
}
