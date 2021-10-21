using CsvHelper;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;

namespace FinanceVisualization.Helpers
{
    public static class FirmInfoHelper
    {
        private static List<FirmInfo> firmInfos;

        static FirmInfoHelper()
        {
            using (var reader = new StreamReader("firms_joined_v2.csv"))
            using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
            {
                csv.Configuration.HasHeaderRecord = false;
                csv.Configuration.MissingFieldFound = null;
                firmInfos = csv.GetRecords<FirmInfo>().ToList();
            }
        }

        public static List<FirmInfo> GetFirmInfos()
        {
            return firmInfos;
        }

    }
}
