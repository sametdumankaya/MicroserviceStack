using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class Event
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public DateTime EventDateTimeStamp { get; set; }

        public DateTime InsertDate { get; set; }

        public string HtmlData { get; set; }

        public string NewsTitle { get; set; }

        public List<IndicatorDetail> IndicatorDetails { get; set; }

        public List<EventPredictor> EventPredictors { get; set; }

        public string EventFlag { get; set; }

        public bool IsGain { get; set; }
     }
}
