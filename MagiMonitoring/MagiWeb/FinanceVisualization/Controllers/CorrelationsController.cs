using FinanceVisualization.Data;
using FinanceVisualization.Helpers;
using FinanceVisualization.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace FinanceVisualization.Controllers
{
    [Authorize]
    [ApiController]
    [Route("[controller]/[action]")]
    public class CorrelationsController : ControllerBase
    {
        private readonly ApplicationDbContext _dbContext;

        public CorrelationsController(ApplicationDbContext dbContext)
        {
            _dbContext = dbContext;
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> PostCorrelations([FromBody] List<NewCorrelation> newCorrelations)
        {
            var correlationsToSave = new List<Correlation>();

            foreach (var item in newCorrelations)
            {
                _dbContext.Correlations.RemoveRange(_dbContext.Correlations.Where(x => x.CorrelationDateTimeStamp.Equals(UnixDateTimeHelper.FromUnixTime(item.correlationDateTimeStampEpochs))));

                var jsonString = JsonConvert.SerializeObject(item);
                correlationsToSave.Add(new Correlation 
                {
                    CorrelationDateTimeStamp = UnixDateTimeHelper.FromUnixTime(item.correlationDateTimeStampEpochs),
                    Title = item.title,
                    InsertDate = DateTime.Now,
                    JsonData = jsonString
                });
            }

            await _dbContext.Correlations.AddRangeAsync(correlationsToSave);
            await _dbContext.SaveChangesAsync();
            return Ok();
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> GetAll([FromBody] GetCorrelationsRequest getCorrelationsRequest)
        {
            var query = _dbContext.Correlations.AsQueryable();

            if (getCorrelationsRequest.startDate.HasValue)
            {
                query = _dbContext.Correlations.Where(x => x.CorrelationDateTimeStamp >= getCorrelationsRequest.startDate.Value && x.CorrelationDateTimeStamp <= getCorrelationsRequest.startDate.Value.AddDays(1));
            }

            var result = await query.ToListAsync();
            return Ok(result);
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> DeleteCorrelations([FromBody] DeleteCorrelationsRequest request)
        {
            if(request == null)
            {
                return BadRequest("Request cannot be null");
            }

            if(request.startDate == null || request.endDate == null)
            {
                return BadRequest("Start and end dates cannot be null");
            }

            if(request.startDate > request.endDate)
            {
                return BadRequest("Start date cannot be later than end date");
            }

            _dbContext.Correlations.RemoveRange(_dbContext.Correlations.Where(x => x.CorrelationDateTimeStamp <= request.endDate && x.CorrelationDateTimeStamp >= request.startDate));
            await _dbContext.SaveChangesAsync();
            return Ok();
        }
    }

    public class NewCorrelation
    {
        public long correlationDateTimeStampEpochs { get; set; }

        public string title { get; set; }

        public List<string> x { get; set; }

        public List<string> y { get; set; }

        public List<List<float>> z { get; set; }
    }

    public class GetCorrelationsRequest
    {
        public DateTime? startDate { get; set; }
    }

    public class DeleteCorrelationsRequest
    {
        public DateTime startDate { get; set; }

        public DateTime endDate { get; set; }
    }
}
