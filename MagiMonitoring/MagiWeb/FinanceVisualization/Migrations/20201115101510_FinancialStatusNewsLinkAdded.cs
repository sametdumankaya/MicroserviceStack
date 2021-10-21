using System;
using Microsoft.EntityFrameworkCore.Migrations;

namespace FinanceVisualization.Migrations
{
    public partial class FinancialStatusNewsLinkAdded : Migration
    {
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "HtmlData",
                table: "FinancialStatuses");

            migrationBuilder.AddColumn<DateTime>(
                name: "InsertDate",
                table: "FinancialStatuses",
                nullable: false,
                defaultValue: new DateTime(1, 1, 1, 0, 0, 0, 0, DateTimeKind.Unspecified));

            migrationBuilder.AddColumn<string>(
                name: "NewsLink",
                table: "FinancialStatuses",
                nullable: true);
        }

        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "InsertDate",
                table: "FinancialStatuses");

            migrationBuilder.DropColumn(
                name: "NewsLink",
                table: "FinancialStatuses");

            migrationBuilder.AddColumn<string>(
                name: "HtmlData",
                table: "FinancialStatuses",
                type: "longtext CHARACTER SET utf8mb4",
                nullable: true);
        }
    }
}
