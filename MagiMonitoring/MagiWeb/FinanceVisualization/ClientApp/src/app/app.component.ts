import { Component, Inject, OnInit } from '@angular/core';
import { MessageService } from 'primeng/api';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { JoyrideService } from 'ngx-joyride';
import { NgcCookieConsentService } from 'ngx-cookieconsent';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html'
})
export class AppComponent implements OnInit {
  title = 'app';
  displayFeedbackModal = false;
  userFeedback = "";

  baseUrl: string;

  constructor(@Inject('BASE_URL') baseUrl: string,
    private messageService: MessageService,
    private http: HttpClient,
    private spinner: NgxSpinnerService,
    private joyrideService: JoyrideService,
    private ccService: NgcCookieConsentService) {
    this.baseUrl = baseUrl;
  }

  ngOnInit(): void {
    this.checkSession();
  }

  submitFeedback() {
    this.spinner.show();
    this.http.post<any>(this.baseUrl + 'Feedback/PostFeedback', {
      "feedbackData": this.userFeedback,
    }).subscribe(result => {
      this.spinner.hide();
      this.displayFeedbackModal = false;
      this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'Your feedback is sent.', life: 3000 });
    }, error => console.error(error));
  }

  feedbackClicked() {
    this.displayFeedbackModal = true;
    this.userFeedback = "";
  }

  setCookie(c_name, value, exdays) {
    var exdate = new Date();
    exdate.setDate(exdate.getDate() + exdays);
    var c_value = escape(value) + ((exdays == null) ? "" : "; expires=" + exdate.toUTCString());
    document.cookie = c_name + "=" + c_value;
  }

  getCookie(c_name) {
    var c_value = document.cookie;
    var c_start = c_value.indexOf(" " + c_name + "=");
    if (c_start == -1) {
      c_start = c_value.indexOf(c_name + "=");
    }
    if (c_start == -1) {
      c_value = null;
    } else {
      c_start = c_value.indexOf("=", c_start) + 1;
      var c_end = c_value.indexOf(";", c_start);
      if (c_end == -1) {
        c_end = c_value.length;
      }
      c_value = unescape(c_value.substring(c_start, c_end));
    }
    return c_value;
  }

  checkSession() {
    var c = this.getCookie("visited");
    if (c !== "yes") {
      this.joyrideService.startTour({
        steps: [
          'step1',
          //'step2',
          'step3',
          'step4',
          'step5',
          'step6'
        ]
      });
    }
    this.setCookie("visited", "yes", 365 * 50); // expire in 1 year; or use null to never expire
  }
}
