using System;
using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class Correlation
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public DateTime InsertDate { get; set; }

        public DateTime CorrelationDateTimeStamp { get; set; }

        public string Title { get; set; }

        public string JsonData { get; set; }
    }
}
