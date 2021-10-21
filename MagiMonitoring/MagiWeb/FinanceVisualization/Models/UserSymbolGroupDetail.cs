using System.ComponentModel.DataAnnotations.Schema;

namespace FinanceVisualization.Models
{
    public class UserSymbolGroupDetail
    {
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public int Id { get; set; }

        public string Symbol { get; set; }

        public int UserSymbolGroupId { get; set; }

        public UserSymbolGroup UserSymbolGroup { get; set; }
    }
}
