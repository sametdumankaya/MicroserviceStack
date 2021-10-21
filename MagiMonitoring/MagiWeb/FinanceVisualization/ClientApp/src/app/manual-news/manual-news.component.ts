import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { MessageService, ConfirmationService } from 'primeng/api';
import { AngularEditorConfig } from '@kolkov/angular-editor';

@Component({
  selector: 'app-manual-news',
  templateUrl: './manual-news.component.html'
})
export class ManualNewsComponent {
  baseUrl: string;
  title = "";
  text = "";
  id = 0;

  config: AngularEditorConfig = {
    editable: true,
    spellcheck: true,
    minHeight: '60vh',
    width: '60vw',
    placeholder: 'Enter news here...',
    translate: 'no',
    defaultParagraphSeparator: 'p',
    defaultFontName: 'Arial',
    sanitize: false
  };

  manualNews: any[] = [];
  selectedManualNews: any[] = [];
  manualNewsDialog = false;

  constructor(private http: HttpClient,
    @Inject('BASE_URL') baseUrl: string,
    private spinner: NgxSpinnerService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService) {
    this.baseUrl = baseUrl;
    this.initManualNewsTable();
  }

  initManualNewsTable() {
    this.spinner.show();
    this.http.get<any>(this.baseUrl + 'ManualNews/GetAllUserNews').subscribe(result => {
      this.manualNews = result;
      this.spinner.hide();
    }, error => {
      this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: error.error, life: 3000 });
      this.spinner.hide();
    });
  }

  openNew() {
    this.id = 0;
    this.title = null;
    this.text = null;
    this.manualNewsDialog = true;
  }

  deleteSelectedManualNews() {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete selected news?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.spinner.show();
        this.http.post<any>(this.baseUrl + 'ManualNews/DeleteManualNews', {
          "ids": this.selectedManualNews.map(function (a) { return a["id"]; })
        }).subscribe(result => {
          this.selectedManualNews = [];
          this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'News deleted.', life: 3000 });
          this.spinner.hide();
          this.initManualNewsTable();
        }, error => {
          this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: error.error, life: 3000 });
          this.spinner.hide();
        });
      }
    });
  }

  deleteManualNews(manualNews) {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete this news?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.spinner.show();
        this.http.post<any>(this.baseUrl + 'ManualNews/DeleteManualNews', {
          "ids": [manualNews.id]
        }).subscribe(result => {
          this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'News deleted.', life: 3000 });
          this.spinner.hide();
          this.initManualNewsTable();
        }, error => {
          this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: error.error, life: 3000 });
          this.spinner.hide();
        });
      }
    });
  }

  editManualNews(manualNews) {
    this.id = manualNews.id;
    this.title = manualNews.title;
    this.text = manualNews.htmlData;
    this.manualNewsDialog = true;
  }

  hideDialog() {
    this.manualNewsDialog = false;
  }

  getManualNewsSummary(htmlData) {
    let tmp = document.createElement("DIV");
    tmp.innerHTML = htmlData;
    let result = tmp.textContent || tmp.innerText || "";
    return result.length > 60 ? result.substring(0, 60) + "..." : result;
  }

  getManualNewsTitleSummary(title: string) {
    return title.length > 30 ? title.substring(0, 30) + "..." : title;
  }

  saveManualNews() {
    if (this.text == null || this.text.trim() === "") {
      this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: 'News data cannot be empty or white space.', life: 3000 });
      return;
    }

    if (this.id > 0) {
      this.confirmationService.confirm({
        message: 'Are you sure you want to update this news?',
        header: 'Confirm',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.spinner.show();
          this.http.post<any>(this.baseUrl + 'ManualNews/UpdateManualNews', {
            "id": this.id,
            "title": this.title,
            "htmlData": this.text
          }).subscribe(result => {
            this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'News updated.', life: 3000 });
            this.spinner.hide();
            this.hideDialog();
            this.initManualNewsTable();
          }, error => {
            this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: error.error, life: 3000 });
            this.spinner.hide();
          });
        }
      });
    } else {
      this.confirmationService.confirm({
        message: 'Are you sure you want to save this news?',
        header: 'Confirm',
        icon: 'pi pi-exclamation-triangle',
        accept: () => {
          this.spinner.show();
          this.http.post<any>(this.baseUrl + 'ManualNews/PostManualNews', {
            "title": this.title,
            "htmlData": this.text
          }).subscribe(result => {
            this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'News saved.', life: 3000 });
            this.spinner.hide();
            this.hideDialog();
            this.initManualNewsTable();
          }, error => {
            this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: error.error, life: 3000 });
            this.spinner.hide();
          });
        }
      });
    }   
  }
}

