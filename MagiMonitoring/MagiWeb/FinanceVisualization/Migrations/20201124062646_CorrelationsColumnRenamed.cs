using Microsoft.EntityFrameworkCore.Migrations;

namespace FinanceVisualization.Migrations
{
    public partial class CorrelationsColumnRenamed : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "PlotHtml",
                table: "Correlations");

            migrationBuilder.AddColumn<string>(
                name: "JsonData",
                table: "Correlations",
                nullable: true);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "JsonData",
                table: "Correlations");

            migrationBuilder.AddColumn<string>(
                name: "PlotHtml",
                table: "Correlations",
                type: "longtext CHARACTER SET utf8mb4",
                nullable: true);
        }
    }
}
