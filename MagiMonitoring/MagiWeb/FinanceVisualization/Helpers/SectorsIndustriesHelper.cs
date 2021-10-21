using AngleSharp;
using FinanceVisualization.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace FinanceVisualization.Helpers
{
    public static class SectorsIndustriesHelper
    {
        public async static Task<List<SectorIndustryInfo>> GetSectorsInfoAsync()
        {
            var config = Configuration.Default.WithDefaultLoader();
            var context = BrowsingContext.New(config);

            var sectorDocument = await context.OpenAsync("https://eresearch.fidelity.com/eresearch/markets_sectors/PerformanceSector.jhtml");
            var sectors = sectorDocument.QuerySelectorAll("body > table > tbody > tr > th > div > a").Select(x => x.TextContent.Trim()).ToList();
            var sectorsLastPercentageChanges = sectorDocument.QuerySelectorAll("body > table > tbody > tr > td:nth-child(2) > div").Select(x => x.TextContent.Trim()).ToList();
            var sectorsMarketCaps = sectorDocument.QuerySelectorAll("body > table > tbody > tr > td:nth-child(3)").Select(x => x.TextContent.Trim()).ToList();
            var sectorsOneYearChanges = sectorDocument.QuerySelectorAll("body > table > tbody > tr > td.last-col > span:nth-child(2)").Select(x => x.TextContent.Trim()).ToList();

            var sectorsInfo = new List<SectorIndustryInfo>();
            for (int i = 0; i < sectors.Count; i++)
            {
                sectorsInfo.Add(new SectorIndustryInfo
                {
                    Name = sectors[i],
                    LastPercentageChange = sectorsLastPercentageChanges[i],
                    MarketCap = sectorsMarketCaps[i],
                    OneYearPercentageChange = sectorsOneYearChanges[i]
                });
            }

            return sectorsInfo;
        }

        public async static Task<List<SectorIndustryInfo>> GetIndustriesInfoAsync()
        {
            var config = Configuration.Default.WithDefaultLoader();
            var context = BrowsingContext.New(config);

            var industryDocument = await context.OpenAsync("https://eresearch.fidelity.com/eresearch/markets_sectors/PerformanceIndustries.jhtml");
            var industries = industryDocument.QuerySelectorAll("#tableSort > tbody > tr > th > a").Select(x => x.TextContent.Trim()).ToList();
            var industriesLastPercentageChanges = industryDocument.QuerySelectorAll("#tableSort > tbody > tr > td:nth-child(2) > span").Select(x => x.TextContent.Trim()).ToList();
            var industriesMarketCaps = industryDocument.QuerySelectorAll("#tableSort > tbody > tr > td:nth-child(3)").Select(x => x.TextContent.Trim()).ToList();
            var industriesOneYearChanges = industryDocument.QuerySelectorAll("#tableSort > tbody > tr > td.last-col > span").Select(x => x.TextContent.Trim()).ToList();

            var industriesInfo = new List<SectorIndustryInfo>();
            for (int i = 0; i < industries.Count; i++)
            {
                industriesInfo.Add(new SectorIndustryInfo
                {
                    Name = industries[i],
                    LastPercentageChange = industriesLastPercentageChanges[i],
                    MarketCap = industriesMarketCaps[i],
                    OneYearPercentageChange = industriesOneYearChanges[i]
                });
            }

            return industriesInfo;
        }
    }
}
