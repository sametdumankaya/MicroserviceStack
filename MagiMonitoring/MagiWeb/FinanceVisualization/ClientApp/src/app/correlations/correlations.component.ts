import { Component, Inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { DatePipe } from '@angular/common';


@Component({
  selector: 'app-correlations',
  templateUrl: './correlations.component.html'
})
export class CorrelationsComponent {
  correlations: any[];
  baseUrl: string;
  layout: any;

  startDate = new Date();

  constructor(private http: HttpClient,
    @Inject('BASE_URL') baseUrl: string,
    private datePipe: DatePipe,
    private spinner: NgxSpinnerService) {
    this.baseUrl = baseUrl;
    this.layout = {
      autosize: true,
      yaxis: {
        automargin: true,
        tickangle: "auto"
      },
      xaxis: {
        automargin: true,
        tickangle: -45
      },
      font: {
        size: 10
      },
      margin: { t: 90, r: 0, b: 0, l: 0 }
    };
    this.filterData();
  }

  filterData() {
    this.spinner.show();
    this.http.post<any[]>(this.baseUrl + 'Correlations/GetAll', {
      "startDate": this.startDate != null ? this.datePipe.transform(this.startDate, "yyyy-MM-dd") : null
    }).subscribe(result => {
      result.forEach(r =>
      {
        r.jsonData = JSON.parse(r.jsonData);

        let text = r["jsonData"]["z"].map((row, i) => row.map((item, j) => {
          return ` x: ${r["jsonData"]["y"][j]}<br> y: ${r["jsonData"]["x"][i]}<br> Value: ${item.toFixed(4)}`
        }))

        r["data"] = [
          {
            z: r["jsonData"]["z"],
            x: r["jsonData"]["x"],
            y: r["jsonData"]["y"],
            type: 'heatmap',
            text: text,
            hoverinfo: 'text'
          }
        ];
              
      });
      this.correlations = result;
      this.spinner.hide();
    }, error => console.error(error));
  }

  isCorrelationsDataAvailable() {
    return this.correlations != null && this.correlations.length > 0;
  }
}


