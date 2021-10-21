import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { MessageService } from 'primeng/api';
import { DatePipe, DecimalPipe } from '@angular/common';
import 'chartjs-plugin-zoom'

@Component({
  selector: 'app-finance-news',
  templateUrl: './finance-news.component.html'
})
export class FinanceNewsComponent {
  @ViewChild('barChart', { static: false }) barChart;
  today: number = Date.now();

  baseUrl: string;
  events: Event[];
  chartData: any;
  options: any;

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

  userSymbolGroups: any[] = [];
  selectedUserSymbolGroup: any;

  eventFlags: any[] = [];
  selectedEventFlag: any;

  gainLossOptions: any[] = [];
  selectedGainLoss: any;

  zoomSpeed = 0.7;
  panSpeed = 2000;

  constructor(private http: HttpClient,
    @Inject('BASE_URL') baseUrl: string,
    private spinner: NgxSpinnerService,
    private messageService: MessageService,
    private datePipe: DatePipe,
    private decimalPipe: DecimalPipe) {
    this.options = {
      title: {
        display: true,
        text: 'EVENT ANALYSIS'
      },
      legend: {
        labels: {
          filter: function (legendItem, data) {
            var sum = data.datasets[legendItem.datasetIndex].data.reduce((acc, cur) => acc + cur, 0);
            return sum != 0;
          }
        }
      },
      tooltips: {
        itemSort: (a, b, data) => Number(b.yLabel) - Number(a.yLabel),
        yAlign: 'bottom',
        mode: 'index',
        //mode: 'point',
        intersect: false,
        callbacks: {
          label: function (t, d) {
            var dstLabel = d.datasets[t.datasetIndex].label;
            var yLabel = t.yLabel;
            return Number(yLabel) != 0 ? dstLabel + ': $ ' + decimalPipe.transform(Number(yLabel)) : null;
          }
        }
      },
      hover: {
        mode: 'nearest'
      },
      responsive: true,
      scales: {
        xAxes: [{
          stacked: true,
          scaleLabel: {
            display: true,
            labelString: 'Event Date',
            padding: 20
          },
          ticks: {
            autoSkip: false,
            maxRotation: 90,
            minRotation: 90
          }
        }],
        yAxes: [{
          stacked: true,
          scaleLabel: {
            display: true,
            labelString: 'Market Cap'
          }
        }]
      },
      plugins: {
        zoom: {
          pan: {
            enabled: false,
            mode: 'xy',
            speed: this.panSpeed
          },
          zoom: {
            enabled: true,
            mode: 'xy',
            speed: this.zoomSpeed,
            drag: true
          }
        }
      }
    };

    this.startDateTime = new Date();
    this.startDateTime.setHours(0, 0);

    this.baseUrl = baseUrl;
    this.initSectorsDropdown();
    this.initIndicatorsDropdown();
    this.initChartTypeDropdown();
    this.initUserSymbolGroupsDropdown();
    this.initEventFlagsDropdown();
    this.initChartData();
    this.initGainLossDropdown();
  }

  initGainLossDropdown() {
    this.gainLossOptions = [
      { name: 'Gain' },
      { name: 'Loss' },
      { name: 'All' }
    ];

    this.selectedGainLoss = { name: 'All' };
  }

  initEventFlagsDropdown() {
    this.eventFlags = [
      { name: 'Volume' },
      { name: 'Price' },
      { name: 'Combined' }
    ];

    this.selectedEventFlag = { name: 'Price' };
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

  initChartTypeDropdown() {
    this.chartTypes = [
      { name: 'Sector Based Chart' },
      { name: 'Industry Based Chart' },
      { name: 'Company Based Chart' }
    ];
    this.selectedChartType = { name: 'Company Based Chart' };
  }

  onEventTypeDropdownChange(event) {
    this.onChartTypeDropdownChange(event);
  }

  onChartTypeDropdownChange(event) {
    if (this.selectedChartType.name == 'Sector Based Chart') {
      this.updateBarChart("sector");
    } else if (this.selectedChartType.name == 'Industry Based Chart') {
      this.updateBarChart("industry");
    } else if (this.selectedChartType.name == 'Company Based Chart') {
      this.updateBarChart("symbol");
    } else {
      this.updateBarChart("sector");
    }
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
      "eventFlag": this.selectedEventFlag != null ? this.selectedEventFlag["name"] : null,
      "onlyPredictives": false,
      "isGain": null
    }).subscribe(result => {
      this.events = result;
      this.onChartTypeDropdownChange(null);
      this.spinner.hide();
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
      let isGain = null;
      if (this.selectedGainLoss != null) {
        if (this.selectedGainLoss["name"] == "Gain") {
          isGain = true;
        }
        else if (this.selectedGainLoss["name"] == "Loss") {
          isGain = false;
        }
        else {
          isGain = null;
        }
      }
      this.http.post<Event[]>(this.baseUrl + 'Events/GetAll', {
        "startDateTime": this.datePipe.transform(this.startDateTime, "yyyy-MM-dd"),
        "sectorNames": this.selectedSectors.map(function (a) { return a["name"]; }),
        "industryNames": this.selectedIndustries.map(function (a) { return a["name"]; }),
        "minMarketCap": this.minMarketCap,
        "maxMarketCap": this.maxMarketCap,
        "indicatorTypes": this.selectedIndicators.map(function (a) { return a["name"]; }),
        "userSymbolGroupId": this.selectedUserSymbolGroup != null ? this.selectedUserSymbolGroup.id : null,
        "eventFlag": this.selectedEventFlag != null ? this.selectedEventFlag["name"] : null,
        "onlyPredictives": false,
        "isGain": isGain
      }).subscribe(result => {
        this.events = result;
        this.onChartTypeDropdownChange(null);
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

  // baseField: name of the field that contains the values of variables that is going to be base of the chart. (e.g sector, industry, symbol)
  updateBarChart(baseField: string) {
    this.sectorMarketCapitals = [];
    var distinctList = [];
    this.distinctEventDateTimeStamps = [];

    var currentSelectedIndicators = [];

    if (this.selectedIndicators.length == 0) {
      currentSelectedIndicators = this.indicatorOptions;
    } else {
      currentSelectedIndicators = this.selectedIndicators;
    }

    if (currentSelectedIndicators.find(x => x.name == '') == null) {
      currentSelectedIndicators.push({
        name: ''
      });
    }

    this.events.forEach(e => {
      if (!(e.indicatorDetails.length == 1 && e.indicatorDetails[0].eventRole === "")) {
        e.indicatorDetails.forEach(idetail => {
          //if (e.eventFlag != null && e.eventFlag != "") {
          this.sectorMarketCapitals.push({
            eventDateTimeStamp: this.datePipe.transform(new Date(e.eventDateTimeStamp), "yyyy-MM-dd HH:mm:ss"),
            eventRole: idetail.eventRole,
            industry: idetail.firmInfo != null ? idetail.firmInfo.industry : "UNKNOWN",
            sector: idetail.firmInfo != null ? idetail.firmInfo.sector : "UNKNOWN",
            symbol: idetail.symbol,
            volume: idetail.volume,
            price: idetail.price
          });
          //}      
        });
      }    
    });

    this.sectorMarketCapitals.forEach(smc => {
      if (!distinctList.includes(smc[baseField])) {
        distinctList.push(smc[baseField]);
      }
      if (!this.distinctEventDateTimeStamps.includes(smc.eventDateTimeStamp)) {
        let tempEvent = this.events.find(x => this.datePipe.transform(new Date(x.eventDateTimeStamp), "yyyy-MM-dd HH:mm:ss") === smc.eventDateTimeStamp);
        if (tempEvent.indicatorDetails != null && tempEvent.indicatorDetails.length > 0) {
          this.distinctEventDateTimeStamps.push(smc.eventDateTimeStamp);
        }
      }
    });

    let myData = [];

    this.distinctEventDateTimeStamps.forEach(dedts => {
      let temp = [];
      distinctList.forEach(d => {
        let indicatorTemp = [];
        for (var i = 0; i < currentSelectedIndicators.length; i++) {
          var totalCap = 0;
          this.sectorMarketCapitals.forEach(smc => {
            if (smc.eventDateTimeStamp == dedts && smc[baseField] == d && smc.eventRole == currentSelectedIndicators[i].name) {
              totalCap += smc.volume * smc.price;
            }
          });
          indicatorTemp.push(totalCap);
        }
        temp.push(indicatorTemp);
      });
      myData.push(temp);
    });

    let datasets = [];
    for (var i = 0; i < distinctList.length; i++) {
      let curr_data = [];
      for (var j = 0; j < this.distinctEventDateTimeStamps.length; j++) {
        curr_data.push(myData[j][i]);
      }

      for (var k = 0; k < currentSelectedIndicators.length; k++) {
        let curr_indicator_volumes = [];
        curr_data.forEach(cd => {
          curr_indicator_volumes.push(cd[k]);
        });

        if (curr_indicator_volumes.reduce((acc, cur) => acc + cur, 0) != 0) {
          datasets.push({
            label: distinctList[i] + " - " + currentSelectedIndicators[k].name.substr(0, currentSelectedIndicators[k].name.indexOf(' ')),
            backgroundColor: "#000000".replace(/0/g, function () { return (~~(Math.random() * 16)).toString(16); }),
            data: curr_indicator_volumes,
            barPercentage: 0.85,
            stack: currentSelectedIndicators[k].name,
          });
        }
      }
    }

    this.chartData = {
      labels: this.distinctEventDateTimeStamps,
      datasets: datasets
    };
  }

  selectData(event) {
    let selectedDateTimeStamp = this.distinctEventDateTimeStamps[event.element._index]
    this.selectedEvent = this.events.find(x => this.datePipe.transform(new Date(x.eventDateTimeStamp), "yyyy-MM-dd HH:mm:ss") === selectedDateTimeStamp);
    this.selectedEvent.indicatorDetails.sort((a, b) => a.volume > b.volume ? -1 : a.volume < b.volume ? 1 : 0);
    this.displayModalEvent = true;
  }

  isChartDataAvailable() {
    return this.chartData != null && this.chartData.datasets.length > 0
  }

  resetZoomState() {
    this.barChart.chart.resetZoom();
  }
}

export interface FirmInfo {
  source: string,
  target: string,
  sector: string,
  fullTimeEmployees: number,
  longBusinessSummary: string,
  website: string,
  industry: string
}

export interface IndicatorDetail {
  id: number,
  symbol: string,
  volume: number,
  price: number,
  eventRole: string,
  eventId: number,
  firmInfo: FirmInfo
}

export interface EventPredictor {
  id: number,
  symbol: string,
  predictivePower: number,
  timeStamp: string,
  eventId: number
}

export interface Event {
  id: number,
  eventDateTimeStamp: string,
  insertDate: string,
  htmlData: string,
  newsTitle: string,
  eventFlag: string,
  indicatorDetails: IndicatorDetail[],
  eventPredictors: EventPredictor[]
}

export interface BarChartDataTemplate {
  eventDateTimeStamp: string,
  symbol: string,
  volume: number,
  price: number,
  eventRole: string,
  sector: string,
  industry: string
}
