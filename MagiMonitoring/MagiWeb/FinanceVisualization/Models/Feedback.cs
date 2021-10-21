using System;
using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class Feedback
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public DateTime InsertDate { get; set; }

        public string FeedbackData { get; set; }
    }
}
