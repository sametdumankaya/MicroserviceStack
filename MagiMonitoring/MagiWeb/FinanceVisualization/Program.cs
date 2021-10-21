using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Hosting;
using Serilog;
using Serilog.Exceptions;
using Serilog.Formatting.Json;

namespace FinanceVisualization
{
    public class Program
    {
        public static void Main(string[] args)
        {
            Log.Logger = new LoggerConfiguration().Enrich
                                                  .WithExceptionDetails()
                                                  .WriteTo
                                                  .File(new JsonFormatter(), 
                                                       //"Logs/magifinance_log_.json",
                                                       "/home/samet/Logs/magifinance_log_.json",
                                                       rollingInterval: RollingInterval.Day)
                                                  .CreateLogger();
            CreateHostBuilder(args).Build().Run();
        }

        public static IHostBuilder CreateHostBuilder(string[] args) =>
            Host.CreateDefaultBuilder(args)
                .ConfigureWebHostDefaults(webBuilder =>
                {
                    webBuilder.UseStartup<Startup>();
                });
    }
}
