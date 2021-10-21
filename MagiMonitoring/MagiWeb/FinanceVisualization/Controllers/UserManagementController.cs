using FinanceVisualization.Data;
using FinanceVisualization.Helpers;
using FinanceVisualization.Models;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.Linq;
using System.Security.Claims;
using System.Threading.Tasks;

namespace FinanceVisualization.Controllers
{
    [Authorize]
    [ApiController]
    [Route("[controller]/[action]")]
    public class UserManagementController : ControllerBase
    {
        private readonly UserManager<ApplicationUser> _userManager;
        private readonly ApplicationDbContext _dbContext;

        public UserManagementController(UserManager<ApplicationUser> userManager, ApplicationDbContext dbContext)
        {
            _userManager = userManager;
            _dbContext = dbContext;
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> GetAll()
        {
            var result = await _userManager.Users.ToListAsync();
            return Ok(result);
        }

        [AllowAnonymous]
        [HttpPost]
        public async Task<IActionResult> DeleteUser([FromBody] DeleteUserRequest deleteUserRequest)
        {
            var user = await _userManager.FindByIdAsync(deleteUserRequest.id);
            _dbContext.UserSymbolGroups.RemoveRange(_dbContext.UserSymbolGroups.Where(x => x.UserId.Equals(user.Id)));
            _dbContext.ManualNews.RemoveRange(_dbContext.ManualNews.Where(x => x.UserId.Equals(user.Id)));
            IdentityResult result = await _userManager.DeleteAsync(user);
            return result.Succeeded ? (IActionResult)Ok() : NotFound();
        }

        [HttpGet]
        public async Task<IActionResult> IsAuthenticated()
        {
            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var user = await _userManager.FindByIdAsync(userId);
            var result = RegistrationHelper.IsAuthenticatedForChangingRegistration(user.Email.ToLower());
            return Ok(result);
        }

        [AllowAnonymous]
        [HttpGet]
        public async Task<IActionResult> GetRegistrationStatus()
        {
            var result = await _dbContext.RegistrationSettings.FirstOrDefaultAsync();

            if (result == null)
            {
                _dbContext.RegistrationSettings.Add(new RegistrationSetting()
                {
                    Status = true
                });
                await _dbContext.SaveChangesAsync();
                return Ok(true);
            }
            else
            {
                return Ok(result.Status);
            }
        }

        [HttpPost]
        public async Task<IActionResult> UpdateRegistrationStatus([FromBody] UpdateRegistrationStatusRequest request)
        {
            if (request == null)
            {
                return BadRequest("You must submit a registration status.");
            }

            var userId = User.FindFirstValue(ClaimTypes.NameIdentifier);
            var user = await _userManager.FindByIdAsync(userId);

            if (RegistrationHelper.IsAuthenticatedForChangingRegistration(user.Email.ToLower()))
            {
                var result = await _dbContext.RegistrationSettings.FirstOrDefaultAsync();

                if (result == null)
                {
                    _dbContext.RegistrationSettings.Add(new RegistrationSetting()
                    {
                        Status = request.status
                    });
                }
                else
                {
                    result.Status = request.status;
                }

                await _dbContext.SaveChangesAsync();
                return Ok(request.status);
            }
            else
            {
                return Unauthorized("You are not authorized to update registration status.");
            }
        }

        [HttpPost]
        public async Task<IActionResult> UpdateUserManualNewsPermission([FromBody] UpdateUserManualNewsPermissionRequest request)
        {
            if (request == null)
            {
                return BadRequest("You must submit a user manual news permission request.");
            }

            var user = await _userManager.FindByIdAsync(request.id);

            if(user == null)
            {
                return NotFound("User not found");
            }

            user.CanAddNews = !user.CanAddNews;
            await _dbContext.SaveChangesAsync();
            return Ok();
        }
    }

    public class DeleteUserRequest
    {
        public string id { get; set; }
    }

    public class UpdateRegistrationStatusRequest
    {
        public bool status { get; set; }
    }

    public class UpdateUserManualNewsPermissionRequest
    {
        public string id { get; set; }
    }
}
