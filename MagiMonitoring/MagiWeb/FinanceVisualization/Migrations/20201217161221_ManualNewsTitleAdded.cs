using Microsoft.EntityFrameworkCore.Migrations;

namespace FinanceVisualization.Migrations
{
    public partial class ManualNewsTitleAdded : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "Title",
                table: "ManualNews",
                nullable: true);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "Title",
                table: "ManualNews");
        }
    }
}
