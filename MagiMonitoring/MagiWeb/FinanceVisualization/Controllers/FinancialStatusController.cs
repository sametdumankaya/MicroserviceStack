using FinanceVisualization.Data;
using FinanceVisualization.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace FinanceVisualization.Controllers
{
    [Authorize]
    [ApiController]
    [Route("[controller]/[action]")]
    public class FinancialStatusController : ControllerBase
    {
        private readonly ApplicationDbContext _dbContext;

        public FinancialStatusController(ApplicationDbContext dbContext)
        {
            _dbContext = dbContext;
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> PostFinancialStatus([FromBody] List<NewFinancialStatus> newFinancialStatusList)
        {
            if (newFinancialStatusList == null || newFinancialStatusList.Count == 0)
            {
                throw new InvalidOperationException("Cannot post null object.");
            }

            var financialStatusList = new List<FinancialStatus>();
            foreach (var item in newFinancialStatusList)
            {
                financialStatusList.Add(new FinancialStatus 
                { 
                    InsertDate = DateTime.Now,
                    Name = item.name,
                    Type = item.type,
                    StatusValue = item.statusValue,
                    NewsLink = item.newsLink
                });
            }

            await _dbContext.AddRangeAsync(financialStatusList);
            await _dbContext.SaveChangesAsync();
            return Ok();
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> GetAll([FromBody] GetFinancialStatusFilterModel getFinancialStatusFilterModel)
        {
            var query = _dbContext.FinancialStatuses.Where(x => x.InsertDate >= DateTime.Now.AddDays(-3)).AsQueryable();

            if(getFinancialStatusFilterModel != null)
            {
                if(!string.IsNullOrWhiteSpace(getFinancialStatusFilterModel.name))
                {
                    query = query.Where(x => x.Name.ToLower().Contains(getFinancialStatusFilterModel.name.ToLower()));
                }

                if (!string.IsNullOrWhiteSpace(getFinancialStatusFilterModel.type))
                {
                    query = query.Where(x => x.Type.ToLower().Contains(getFinancialStatusFilterModel.type.ToLower()));
                }

                if(getFinancialStatusFilterModel.minStatusValue.HasValue)
                {
                    var currentMin = getFinancialStatusFilterModel.minStatusValue.Value / (double)100;
                    query = query.Where(x => x.StatusValue >= currentMin);
                }

                if (getFinancialStatusFilterModel.maxStatusValue.HasValue)
                {
                    var currentMax = getFinancialStatusFilterModel.maxStatusValue.Value / (double)100;
                    query = query.Where(x => x.StatusValue <= currentMax);
                }

                if(getFinancialStatusFilterModel.userSymbolGroupId.HasValue)
                {
                    var userSymbolGroup = await _dbContext.UserSymbolGroups.Where(x => x.Id == getFinancialStatusFilterModel.userSymbolGroupId).Include(x => x.UserSymbolGroupDetails).FirstOrDefaultAsync();
                    query = query.Where(x => userSymbolGroup.UserSymbolGroupDetails.Select(y => y.Symbol).Contains(x.Name));
                }
            }

            var financialStatusList = await query.ToListAsync();
            return Ok(financialStatusList);
        }
    }

    public class NewFinancialStatus
    {
        public string name { get; set; }

        public string type { get; set; }

        public float statusValue { get; set; }

        public string newsLink { get; set; }
    }

    public class GetFinancialStatusFilterModel
    {
        public string name { get; set; }

        public string type { get; set; }

        public int? minStatusValue { get; set; }

        public int? maxStatusValue { get; set; }

        public int? userSymbolGroupId { get; set; }
    }
}
