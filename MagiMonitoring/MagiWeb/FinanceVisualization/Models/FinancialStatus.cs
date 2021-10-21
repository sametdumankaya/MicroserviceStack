using System;
using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class FinancialStatus
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public DateTime InsertDate { get; set; }

        public string Name { get; set; }

        public string Type { get; set; }

        public float StatusValue { get; set; }

        public string NewsLink { get; set; }
    }
}
