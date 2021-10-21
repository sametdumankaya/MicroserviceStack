using FinanceVisualization.Data;
using FinanceVisualization.Helpers;
using FinanceVisualization.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Internal;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace FinanceVisualization.Controllers
{
    [Authorize]
    [ApiController]
    [Route("[controller]/[action]")]
    public class EventsController : ControllerBase
    {
        private readonly ApplicationDbContext _dbContext;

        public EventsController(ApplicationDbContext dbContext)
        {
            _dbContext = dbContext;
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> PostEvents([FromBody] List<NewEvent> newEventList)
        {
            var eventsToSave = new List<Event>();

            foreach (var newEvent in newEventList)
            {
                _dbContext.Events.RemoveRange(_dbContext.Events.Where(x => x.EventDateTimeStamp.Equals(UnixDateTimeHelper.FromUnixTime(newEvent.EventDateTimeStampEpochs))));

                var currentEventToSave = new Event();
                currentEventToSave.EventDateTimeStamp = UnixDateTimeHelper.FromUnixTime(newEvent.EventDateTimeStampEpochs);
                currentEventToSave.NewsTitle = newEvent.NewsTitle;
                currentEventToSave.HtmlData = newEvent.HtmlData;
                currentEventToSave.InsertDate = DateTime.Now;
                currentEventToSave.IndicatorDetails = new List<IndicatorDetail>();
                currentEventToSave.EventPredictors = new List<EventPredictor>();
                currentEventToSave.EventFlag = newEvent.EventFlag;
                currentEventToSave.IsGain = newEvent.IsGain;

                if (newEvent.Indicators != null)
                {
                    foreach (var item in newEvent.Indicators)
                    {
                        currentEventToSave.IndicatorDetails.Add(new IndicatorDetail()
                        {
                            Symbol = item.Symbol,
                            Volume = item.Volume,
                            Price = item.Price,
                            EventRole = item.EventRole
                        });
                    }
                }

                if (newEvent.EventPredictors != null)
                {
                    foreach (var item in newEvent.EventPredictors)
                    {
                        currentEventToSave.EventPredictors.Add(new EventPredictor
                        {
                            Symbol = item.Symbol,
                            PredictivePower = item.PredictivePower,
                            TimeStamp = item.DateTimeStamp.HasValue && item.DateTimeStamp.Value > 0 ? UnixDateTimeHelper.FromUnixTime(item.DateTimeStamp.Value) : (DateTime?)null
                        });
                    }
                }
                eventsToSave.Add(currentEventToSave);
            }

            await _dbContext.Events.AddRangeAsync(eventsToSave);
            await _dbContext.SaveChangesAsync();
            return Ok();
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> GetAll([FromBody] GetEventsFilterModel getEventsFilterModel)
        {
            var query = _dbContext.Events.AsQueryable();

            if (getEventsFilterModel.onlyPredictives)
            {
                query = _dbContext.Events.Include(x => x.EventPredictors).AsQueryable();
            }
            else
            {
                query = _dbContext.Events.Include(x => x.IndicatorDetails).AsQueryable();
            }

            // Time Filter
            if (getEventsFilterModel.startDateTime != null)
            {
                query = query.Where(x => x.EventDateTimeStamp >= getEventsFilterModel.startDateTime.Value && x.EventDateTimeStamp <= getEventsFilterModel.startDateTime.Value.AddDays(1));
            }

            // Market Capital Filter
            if (getEventsFilterModel.minMarketCap.HasValue)
            {
                query = query.Where(x => x.IndicatorDetails.Sum(y => y.Volume) >= getEventsFilterModel.minMarketCap.Value);
            }

            if (getEventsFilterModel.maxMarketCap.HasValue)
            {
                query = query.Where(x => x.IndicatorDetails.Sum(y => y.Volume) <= getEventsFilterModel.maxMarketCap.Value);
            }

            if (!string.IsNullOrWhiteSpace(getEventsFilterModel.eventFlag))
            {
                query = query.Where(x => x.EventFlag.Equals(getEventsFilterModel.eventFlag) || string.IsNullOrWhiteSpace(x.EventFlag));
            }

            if (getEventsFilterModel.onlyPredictives)
            {
                query = query.Where(x => x.EventPredictors.Any() == getEventsFilterModel.onlyPredictives);
            }

            if (getEventsFilterModel.isGain.HasValue)
            {
                query = query.Where(x => x.IsGain == getEventsFilterModel.isGain.Value);
            }

            query = query.OrderBy(x => x.EventDateTimeStamp);

            var result = await query.ToListAsync();
            var firmInfoList = FirmInfoHelper.GetFirmInfos();

            foreach (var row in result)
            {
                row.HtmlData = System.Net.WebUtility.HtmlDecode(row.HtmlData);

                if (getEventsFilterModel.onlyPredictives)
                {
                    foreach (var item in row.EventPredictors)
                    {
                        item.FirmInfo = firmInfoList.Where(x => x.Source.Equals(item.Symbol)).FirstOrDefault();
                    }
                }
                else
                {
                    foreach (var item in row.IndicatorDetails)
                    {
                        item.FirmInfo = firmInfoList.Where(x => x.Source.Equals(item.Symbol)).FirstOrDefault();
                    }
                }
            }

            if(!getEventsFilterModel.onlyPredictives)
            {
                // Indicator types filter
                if (getEventsFilterModel.indicatorTypes != null && getEventsFilterModel.indicatorTypes.Any())
                {
                    foreach (var item in result)
                    {
                        item.IndicatorDetails = item.IndicatorDetails.Where(x => getEventsFilterModel.indicatorTypes.Contains(x.EventRole)).ToList();
                    }
                }

                // sector names filter
                if (getEventsFilterModel.sectorNames != null && getEventsFilterModel.sectorNames.Any())
                {
                    foreach (var item in result)
                    {
                        item.IndicatorDetails = item.IndicatorDetails.Where(x => getEventsFilterModel.sectorNames.Contains(x.FirmInfo?.Sector)).ToList();
                    }
                }

                // industry names filter
                if (getEventsFilterModel.industryNames != null && getEventsFilterModel.industryNames.Any())
                {
                    foreach (var item in result)
                    {
                        item.IndicatorDetails = item.IndicatorDetails.Where(x => getEventsFilterModel.industryNames.Contains(x.FirmInfo?.Industry)).ToList();
                    }
                }

                // symbols filter
                if (getEventsFilterModel.userSymbolGroupId.HasValue)
                {
                    var userSymbolGroup = await _dbContext.UserSymbolGroups.Where(x => x.Id == getEventsFilterModel.userSymbolGroupId).Include(x => x.UserSymbolGroupDetails).FirstOrDefaultAsync();
                    foreach (var item in result)
                    {
                        item.IndicatorDetails = item.IndicatorDetails.Where(x => userSymbolGroup.UserSymbolGroupDetails.Select(y => y.Symbol).Contains(x.Symbol)).ToList();
                    }
                }

                // top n firms
                foreach (var item in result)
                {
                    var topNIndicatorDetails = new List<IndicatorDetail>();
                    item.IndicatorDetails = item.IndicatorDetails.OrderByDescending(x => x.Volume).ToList();
                    var currentFirstN = item.IndicatorDetails.Take(5).ToList();
                    var currentRemaining = item.IndicatorDetails.Skip(5).ToList();
                    topNIndicatorDetails.AddRange(currentFirstN);
                    topNIndicatorDetails.Add(new IndicatorDetail 
                    { 
                        Id = -1,
                        EventId = item.Id,
                        EventRole = "",
                        Price = currentRemaining.Sum(x => x.Price),
                        Volume = currentRemaining.Sum(x => x.Volume),
                        Symbol = "Other Firms",
                        FirmInfo = new FirmInfo 
                        {
                            Source = "Other Firms",
                            Target = "Other Firms",
                            Sector = "Other Sectors",
                            Website = "",
                            Industry = "Other Industries"
                        }
                    });

                    item.IndicatorDetails = topNIndicatorDetails;
                }
            }

            return Ok(result);
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> UpdateEventNews([FromBody] EventUpdate eventUpdate)
        {
            if (eventUpdate == null || eventUpdate.EventDateTimeStampEpochs == 0)
            {
                return NotFound();
            }

            var currentEvent = await _dbContext.Events.Where(x => x.EventDateTimeStamp == UnixDateTimeHelper.FromUnixTime(eventUpdate.EventDateTimeStampEpochs)).FirstOrDefaultAsync();

            if (currentEvent == null)
            {
                return NotFound();
            }

            currentEvent.HtmlData = eventUpdate.HtmlData;
            currentEvent.NewsTitle = eventUpdate.NewsTitle;
            await _dbContext.SaveChangesAsync();
            return Ok(currentEvent);
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> DeleteEvents([FromBody] DeleteEventsRequest request)
        {
            if (request == null)
            {
                return BadRequest("Request cannot be null");
            }

            if (request.startDate == null || request.endDate == null)
            {
                return BadRequest("Start and end dates cannot be null");
            }

            if (request.startDate > request.endDate)
            {
                return BadRequest("Start date cannot be later than end date");
            }

            _dbContext.Events.RemoveRange(_dbContext.Events.Where(x => x.EventDateTimeStamp <= request.endDate && x.EventDateTimeStamp >= request.startDate));
            await _dbContext.SaveChangesAsync();
            return Ok();
        }
    }

    public class EventUpdate
    {
        public long EventDateTimeStampEpochs { get; set; }

        public string HtmlData { get; set; }

        public string NewsTitle { get; set; }
    }

    public class NewEvent
    {
        public long EventDateTimeStampEpochs { get; set; }

        public string HtmlData { get; set; }

        public string NewsTitle { get; set; }

        public List<NewIndicatorDetail> Indicators { get; set; }

        public List<NewEventPredictor> EventPredictors { get; set; }

        public string EventFlag { get; set; }

        public bool IsGain { get; set; }
    }

    public class NewIndicatorDetail
    {
        public string Symbol { get; set; }

        public float Volume { get; set; }

        public float Price { get; set; }

        public string EventRole { get; set; }
    }

    public class NewEventPredictor
    {
        public string Symbol { get; set; }

        public float PredictivePower { get; set; }

        public long? DateTimeStamp { get; set; }
    }

    public class GetEventsFilterModel
    {
        public DateTime? startDateTime { get; set; }

        public List<string> sectorNames { get; set; }

        public List<string> industryNames { get; set; }

        public int? minMarketCap { get; set; }

        public int? maxMarketCap { get; set; }

        public List<string> indicatorTypes { get; set; }

        public int? userSymbolGroupId { get; set; }

        public string eventFlag { get; set; }

        public bool onlyPredictives { get; set; }

        public bool? isGain { get; set; }
    }

    public class DeleteEventsRequest
    {
        public DateTime startDate { get; set; }

        public DateTime endDate { get; set; }
    }
}
