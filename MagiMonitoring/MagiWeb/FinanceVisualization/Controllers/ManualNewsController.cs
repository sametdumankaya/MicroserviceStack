using FinanceVisualization.Data;
using FinanceVisualization.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Claims;
using System.Threading.Tasks;

namespace FinanceVisualization.Controllers
{
    [Authorize]
    [ApiController]
    [Route("[controller]/[action]")]
    public class ManualNewsController : ControllerBase
    {
        private readonly ApplicationDbContext _dbContext;
        private readonly UserManager<ApplicationUser> _userManager;

        public ManualNewsController(ApplicationDbContext dbContext, UserManager<ApplicationUser> userManager)
        {
            _dbContext = dbContext;
            _userManager = userManager;
        }

        [HttpPost]
        public async Task<IActionResult> PostManualNews([FromBody] NewManualNews newManualNews)
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var user = await _userManager.FindByIdAsync(userId);

            if(!user.CanAddNews)
            {
                return Unauthorized("You are not authorized to post news manually.");
            }

            if (newManualNews == null || string.IsNullOrWhiteSpace(newManualNews.htmlData) || string.IsNullOrWhiteSpace(newManualNews.title))
            {
                return BadRequest("Cannot save an empty title or empty news.");
            }

            var manualNewsToSave = new ManualNews()
            {
                Title = newManualNews.title,
                HtmlData = newManualNews.htmlData,
                InsertDate = DateTime.Now,
                UserId = User.FindFirstValue(ClaimTypes.NameIdentifier)
            };

            await _dbContext.ManualNews.AddAsync(manualNewsToSave);
            await _dbContext.SaveChangesAsync();
            return Ok();
        }

        [HttpGet]
        public async Task<IActionResult> GetAllUserNews()
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var result = await _dbContext.ManualNews.Where(x => x.UserId.Equals(userId)).OrderByDescending(x => x.InsertDate).ToListAsync();
            foreach (var item in result)
            {
                item.HtmlData = System.Net.WebUtility.HtmlDecode(item.HtmlData);
            }
            return Ok(result);
        }

        [HttpGet]
        public async Task<IActionResult> GetAll()
        {
            var result = await _dbContext.ManualNews.OrderByDescending(x => x.InsertDate).ToListAsync();
            foreach (var item in result)
            {
                item.HtmlData = System.Net.WebUtility.HtmlDecode(item.HtmlData);
            }
            return Ok(result);
        }

        [HttpPost]
        public async Task<IActionResult> UpdateManualNews([FromBody] UpdateManualNewsRequest request)
        {
            if (request == null || request.id <= 0 || string.IsNullOrWhiteSpace(request.htmlData) || string.IsNullOrWhiteSpace(request.title))
            {
                return BadRequest("Id must be greater than 0 and title-htmlData should not be empty.");
            }

            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var currentManualNews = _dbContext.ManualNews.Where(x => x.Id == request.id && x.UserId.Equals(userId)).FirstOrDefault();

            if(currentManualNews == null)
            {
                return BadRequest("You cannot update the specified news.");
            }

            currentManualNews.HtmlData = request.htmlData;
            currentManualNews.Title = request.title;
            await _dbContext.SaveChangesAsync();
            return Ok();
        }

        [HttpPost]
        public async Task<IActionResult> DeleteManualNews([FromBody] DeleteManualNewsRequest request)
        {
            if (request == null || request.ids == null || request.ids.Count == 0)
            {
                return BadRequest("There must be at least 1 id.");
            }

            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var currentManualNews = _dbContext.ManualNews.Where(x => request.ids.Contains(x.Id) && x.UserId.Equals(userId));

            _dbContext.ManualNews.RemoveRange(currentManualNews);
            await _dbContext.SaveChangesAsync();
            return Ok();
        }
    }

    public class NewManualNews
    {
        public string title { get; set; }

        public string htmlData { get; set; }
    }

    public class UpdateManualNewsRequest
    {
        public int id { get; set; }

        public string title { get; set; }

        public string htmlData { get; set; }
    }

    public class DeleteManualNewsRequest
    {
        public List<int> ids { get; set; }
    }
}
