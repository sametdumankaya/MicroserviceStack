using FinanceVisualization.Helpers;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;

namespace FinanceVisualization.Controllers
{
    [ApiController]
    [Route("[controller]/[action]")]
    public class SectorsIndustriesController : ControllerBase
    {
        //[HttpGet]
        //public async Task<IActionResult> GetSectorsDetails()
        //{
        //    var result = await SectorsIndustriesHelper.GetSectorsInfoAsync();
        //    return Ok(result);
        //}

        //[HttpGet]
        //public async Task<IActionResult> GetIndustriesDetails()
        //{
        //    var result = await SectorsIndustriesHelper.GetIndustriesInfoAsync();
        //    return Ok(result);
        //}

        [HttpGet]
        public IActionResult GetDistinctSectors()
        {
            var result = FirmInfoHelper.GetFirmInfos().GroupBy(x => x.Sector).Select(grp => grp.First()).Select(x => x.Sector).Where(x => !string.IsNullOrWhiteSpace(x)).ToList();
            return Ok(result);
        }

        [HttpGet]
        public IActionResult GetDistinctIndustries()
        {
            var result = FirmInfoHelper.GetFirmInfos().GroupBy(x => x.Industry).Select(grp => grp.First()).Select(x => x.Industry).Where(x => !string.IsNullOrWhiteSpace(x)).ToList();
            return Ok(result);
        }

        [HttpPost]
        public IActionResult GetIndustriesForSector([FromBody] GetIndustriesModel getIndustriesModel)
        {
            var result = FirmInfoHelper.GetFirmInfos().Where(x => getIndustriesModel.SectorNames.Contains(x.Sector)).Select(x => x.Industry).Distinct().ToList();
            return Ok(result);
        }

        [HttpGet]
        public IActionResult GetDistinctFirmSymbols()
        {
            var result = FirmInfoHelper.GetFirmInfos().Select(x => new { symbol = x.Source, name = x.Target }).Distinct().OrderBy(x => x.symbol).ToList();
            return Ok(result);
        }
    }

    public class GetIndustriesModel
    {
        public List<string> SectorNames { get; set; }
    }
}
