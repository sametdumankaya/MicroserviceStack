import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { MessageService } from 'primeng/api';
import { DatePipe } from '@angular/common';
import { BarChartDataTemplate, Event } from '../finance-news/finance-news.component';

@Component({
  selector: 'app-predictions',
  templateUrl: './predictions.component.html'
})
export class PredictionsComponent {
  today: number = Date.now();
  options: any;
  baseUrl: string;
  events: Event[];

  allCharts: any[];

  sectorMarketCapitals: BarChartDataTemplate[];
  distinctFirms = [];
  distinctSectors = [];
  distinctIndustries = [];
  distinctEventDateTimeStamps = [];

  startDateTime: Date;
  displayModalEvent: boolean;

  selectedEvent: Event;

  // Filter variables
  selectedSectors: any[] = [];
  sectorOptions: any[] = [];

  selectedIndustries: any[] = [];
  industryOptions: any[] = [];

  minMarketCap: number;
  maxMarketCap: number;

  selectedIndicators: any[] = [];
  indicatorOptions: any[] = [];

  chartTypes: any[] = [];
  selectedChartType: any;

  eventTypes: any[] = [];
  selectedEventType: any;

  userSymbolGroups: any[] = [];
  selectedUserSymbolGroup: any;

  constructor(private http: HttpClient, @Inject('BASE_URL') baseUrl: string, private spinner: NgxSpinnerService, private messageService: MessageService, private datePipe: DatePipe) {
    this.options = {
      title: {
        display: true,
      },
      legend: {
        position: 'top',
      },
      responsive: true
    };

    this.startDateTime = new Date();
    this.baseUrl = baseUrl;
    this.initChartData();
    this.initSectorsDropdown();
    this.initIndicatorsDropdown();
    this.initChartTypeDropdown();
    this.initEventTypeDropdown();
    this.initUserSymbolGroupsDropdown();
  }

  initAllCharts() {
    this.allCharts = [];
    this.events.forEach(e => {
      this.allCharts.push(this.prepareDoughnutChart(e));
    });
  }

  isChartDataAvailable() {
    return this.events != null && this.events.length > 0
  }

  predictivePowerClick(event) {
    if (event.htmlData == null || event.htmlData == '' || event.newsTitle == null || event.newsTitle == '') {
      this.messageService.add({ key: 'trToast', severity: 'warn', summary: 'Warning', detail: 'No news available for the specified event.', life: 4000 });
      return;
    }

    this.selectedEvent = event;
    this.selectedEvent.eventPredictors.sort((a, b) => a.predictivePower > b.predictivePower ? -1 : a.predictivePower < b.predictivePower ? 1 : 0);
    this.displayModalEvent = true;
  }

  prepareDoughnutChart(event) {
    let currentData = event.eventPredictors.map(function (a) { return a["predictivePower"]; })
    let currentLabels = event.eventPredictors.map(function (a) { return a["symbol"]; })
    let sumOfPredictors = currentData.reduce((a, b) => a + b, 0)

    if (sumOfPredictors > 0 && sumOfPredictors < 1) {
      currentData.push(Number((1 - sumOfPredictors).toFixed(2)));
      currentLabels.push("UNKNOWN");
    }

    let currentBackgroundColors = [];
    currentData.forEach(d => {
      currentBackgroundColors.push("#000000".replace(/0/g, function () { return (~~(Math.random() * 16)).toString(16); }));
    });

    return {
      labels: currentLabels,
      datasets: [{
        data: currentData,
        backgroundColor: currentBackgroundColors,
        label: 'Dataset 1'
      }]
    };
  }

  initUserSymbolGroupsDropdown() {
    this.http.get<any[]>(this.baseUrl + 'UserSymbolGroup/GetUserSymbolGroups').subscribe(result => {
      this.userSymbolGroups = [];
      result.forEach(grp => {
        this.userSymbolGroups.push({
          id: grp.id,
          name: grp.name,
        });
      });

    }, error => console.error(error));
  }

  initEventTypeDropdown() {
    this.eventTypes = [
      { name: 'Volume' },
      { name: 'Price' },
      { name: 'Combined' }
    ];
    this.selectedEventType = { name: 'Volume' };
  }

  initChartTypeDropdown() {
    this.chartTypes = [
      { name: 'Sector Based Chart' },
      { name: 'Industry Based Chart' },
      { name: 'Company Based Chart' }
    ];
    this.selectedChartType = { name: 'Sector Based Chart' };
  }

  initSectorsDropdown() {
    this.http.get<string[]>(this.baseUrl + 'SectorsIndustries/GetDistinctSectors').subscribe(result => {
      this.sectorOptions = [];
      result.forEach(str => {
        this.sectorOptions.push({
          name: str
        });
      });
    }, error => console.error(error));
  }

  initIndicatorsDropdown() {
    this.indicatorOptions = [];
    this.indicatorOptions.push({
      name: 'Leading Indicator'
    });
    this.indicatorOptions.push({
      name: 'Main Indicator'
    });
    this.indicatorOptions.push({
      name: 'Trailing Indicator'
    });

    this.selectedIndicators.push({
      name: 'Leading Indicator'
    });
    this.selectedIndicators.push({
      name: 'Main Indicator'
    });
    this.selectedIndicators.push({
      name: 'Trailing Indicator'
    });

  }

  initChartData() {
    this.spinner.show();
    this.http.post<Event[]>(this.baseUrl + 'Events/GetAll', {
      "startDateTime": this.datePipe.transform(this.startDateTime, "yyyy-MM-dd"),
      "sectorNames": [],
      "industryNames": [],
      "minMarketCap": null,
      "maxMarketCap": null,
      "indicatorTypes": null,
      "userSymbolGroupId": null,
      "eventFlag": null,
      "onlyPredictives": true
    }).subscribe(result => {
      this.events = result;
      this.spinner.hide();
      this.initAllCharts();
    }, error => console.error(error));
  }

  removeFilters() {
    this.startDateTime = null;
    this.selectedSectors = [];
    this.selectedIndustries = [];
    this.selectedIndustries = [];
    this.minMarketCap = null;
    this.maxMarketCap = null;
    this.selectedIndicators = [];
    this.selectedUserSymbolGroup = null;
  }

  filterData() {
    if (this.startDateTime != null) {
      this.spinner.show();
      this.http.post<Event[]>(this.baseUrl + 'Events/GetAll', {
        "startDateTime": this.datePipe.transform(this.startDateTime, "yyyy-MM-dd"),
        "sectorNames": this.selectedSectors.map(function (a) { return a["name"]; }),
        "industryNames": this.selectedIndustries.map(function (a) { return a["name"]; }),
        "minMarketCap": this.minMarketCap,
        "maxMarketCap": this.maxMarketCap,
        "indicatorTypes": this.selectedIndicators.map(function (a) { return a["name"]; }),
        "userSymbolGroupId": this.selectedUserSymbolGroup != null ? this.selectedUserSymbolGroup.id : null,
        "eventFlag": null,
        "onlyPredictives": true
      }).subscribe(result => {
        this.events = result;
        this.initAllCharts();
        this.spinner.hide();
      }, error => console.error(error));
    } else {
      this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: 'Please select dates and make sure start date is before end date.', life: 4000 });
    }
  }

  onSectorOptionsChange(event) {
    this.spinner.show();
    this.selectedIndustries = [];
    this.http.post<string[]>(this.baseUrl + 'SectorsIndustries/GetIndustriesForSector', {
      SectorNames: this.selectedSectors.map(function (a) { return a["name"]; }),
    }).subscribe(result => {
      this.industryOptions = [];
      result.forEach(str => {
        this.industryOptions.push({
          name: str
        });
      });

      this.spinner.hide();
    }, error => console.error(error));
  }
}
