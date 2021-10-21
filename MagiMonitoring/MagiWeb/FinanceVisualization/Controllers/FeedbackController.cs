using FinanceVisualization.Data;
using FinanceVisualization.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace FinanceVisualization.Controllers
{
    [Authorize]
    [ApiController]
    [Route("[controller]/[action]")]
    public class FeedbackController : ControllerBase
    {
        private readonly ApplicationDbContext _dbContext;

        public FeedbackController(ApplicationDbContext dbContext)
        {
            _dbContext = dbContext;
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> PostFeedback([FromBody] NewFeedback newFeedback)
        {
            var feedbackToSave = new Feedback
            {
                InsertDate = DateTime.Now,
                FeedbackData = newFeedback.FeedbackData
            };

            await _dbContext.Feedbacks.AddAsync(feedbackToSave);
            await _dbContext.SaveChangesAsync();
            return Ok();
        }

        [AllowAnonymous]
        [HttpGet]
        public IActionResult GetFeedbacks()
        {
            var result = _dbContext.Feedbacks.ToList();
            return Ok(result);
        }
    }

    public class NewFeedback
    {
        public string FeedbackData { get; set; }
    }
}
