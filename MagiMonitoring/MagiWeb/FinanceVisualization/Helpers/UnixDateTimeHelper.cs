using System;
using TimeZoneConverter;

namespace FinanceVisualization.Helpers
{
    public static class UnixDateTimeHelper
    {
        public static DateTime FromUnixTime(long unixTime)
        {
                
            TimeZoneInfo pacificZone = TZConvert.GetTimeZoneInfo("Pacific Standard Time");
            var utc = (new DateTime(1970, 1, 1)).AddMilliseconds(unixTime);
            var pacificTime = TimeZoneInfo.ConvertTimeFromUtc(utc, pacificZone);
            return pacificTime;
        }
    }
}
