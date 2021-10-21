using Newtonsoft.Json;

namespace FinanceVisualization.Helpers
{
    public class FirmInfo
    {
        public string Source { get; set; }

        public string Target { get; set; }

        [JsonIgnore]
        public string Concepts { get; set; }

        [JsonIgnore]
        public string Zip { get; set; }

        public string Sector { get; set; }

        [JsonIgnore]
        public float? FullTimeEmployees { get; set; }

        [JsonIgnore]
        public string LongBusinessSummary { get; set; }

        [JsonIgnore]
        public string City { get; set; }

        [JsonIgnore]
        public string Phone { get; set; }

        [JsonIgnore]
        public string State { get; set; }

        [JsonIgnore]
        public string Country { get; set; }

        public string Website { get; set; }

        [JsonIgnore]
        public float? MaxAge { get; set; }

        [JsonIgnore]
        public string Address1 { get; set; }

        public string Industry { get; set; }

        [JsonIgnore]
        public string FullName { get; set; }
    }
}
