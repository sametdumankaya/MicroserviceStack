using Microsoft.EntityFrameworkCore.Migrations;

namespace FinanceVisualization.Migrations
{
    public partial class CorrelationTitleAdded : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Title",
                table: "Correlations",
                nullable: true);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Title",
                table: "Correlations");
        }
    }
}
