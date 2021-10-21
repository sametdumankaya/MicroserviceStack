using FinanceVisualization.Data;
using FinanceVisualization.Models;
using Microsoft.AspNetCore.Authorization;
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
    public class UserSymbolGroupController : ControllerBase
    {
        private readonly ApplicationDbContext _dbContext;

        public UserSymbolGroupController(ApplicationDbContext dbContext)
        {
            _dbContext = dbContext;
        }

        [HttpPost]
        public async Task<IActionResult> PostUserSymbolGroup([FromBody] NewUserSymbolGroup newUserSymbolGroup)
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var userSymbolGroupDetails = new List<UserSymbolGroupDetail>();
            foreach (var item in newUserSymbolGroup.NewUserSymbolGroupDetails)
            {
                userSymbolGroupDetails.Add(new UserSymbolGroupDetail
                {
                    Symbol = item.Symbol
                });
            }
            var userSymbolGroup = new UserSymbolGroup
            {
                InsertDate = DateTime.Now,
                Name = newUserSymbolGroup.Name,
                UserId = userId,
                UserSymbolGroupDetails = userSymbolGroupDetails
            };

            await _dbContext.UserSymbolGroups.AddAsync(userSymbolGroup);
            await _dbContext.SaveChangesAsync();
            return Ok();
        }

        [HttpGet]
        public async Task<IActionResult> GetUserSymbolGroups()
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var result = await _dbContext.UserSymbolGroups.Include(x => x.UserSymbolGroupDetails).Where(x => x.UserId.Equals(userId)).ToListAsync();
            return Ok(result);
        }

        [HttpPost]
        public async Task<IActionResult> DeleteUserSymbolGroups([FromBody] DeleteUserSymbolGroups deleteUserSymbolGroups)
        {
            if (deleteUserSymbolGroups == null || deleteUserSymbolGroups.Ids == null || deleteUserSymbolGroups.Ids.Count == 0)
            {
                return Ok(false);
            }
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            _dbContext.UserSymbolGroups.RemoveRange(deleteUserSymbolGroups.Ids.Select(id => new UserSymbolGroup { Id = id }));
            await _dbContext.SaveChangesAsync();
            return Ok(true);
        }
    }

    public class NewUserSymbolGroup
    {
        public string Name { get; set; }

        public List<NewUserSymbolGroupDetail> NewUserSymbolGroupDetails { get; set; }
    }

    public class NewUserSymbolGroupDetail
    {
        public string Symbol { get; set; }
    }

    public class DeleteUserSymbolGroups
    {
        public List<int> Ids { get; set; }
    }
}
