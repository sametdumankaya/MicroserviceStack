import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { MessageService, ConfirmationService } from 'primeng/api';
import { AngularEditorConfig } from '@kolkov/angular-editor';

@Component({
  selector: 'app-other-news-topics',
  templateUrl: './other-news-topics.component.html'
})
export class OtherNewsTopicsComponent {
  baseUrl: string;
  otherNews: any[] = [];

  editorConfig: AngularEditorConfig = {
    editable: false,
    spellcheck: false,
    enableToolbar: false,
    showToolbar: false,
    sanitize: false
  };

  constructor(private http: HttpClient,
    @Inject('BASE_URL') baseUrl: string,
    private spinner: NgxSpinnerService,
    private messageService: MessageService) {
    this.baseUrl = baseUrl;
    this.initOtherNews();
  }

  initOtherNews() {
    this.spinner.show();
    this.http.get<any>(this.baseUrl + 'ManualNews/GetAll').subscribe(result => {
      this.otherNews = result;
      this.spinner.hide();
    }, error => {
      this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: error.error, life: 3000 });
      this.spinner.hide();
    });
  }

  isOtherNewsTopicsDataAvailable() {
    return this.otherNews != null && this.otherNews.length > 0;
  }
}
