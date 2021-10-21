import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { MessageService } from 'primeng/api';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-financial-status',
  templateUrl: './financial-status.component.html'
})
export class FinancialStatusComponent {
  financialStatuses: any[];
  today: number = Date.now();
  baseUrl: string;

  // Filter variables
  searchName: string;

  minStatusValue: number;
  maxStatusValue: number;
  value1: number;

  financialStatusTypes: any[] = [];
  selectedFinancialStatusType: any;

  userSymbolGroups: any[] = [];
  selectedUserSymbolGroup: any;

  selectedStatus: any;

  constructor(private http: HttpClient, @Inject('BASE_URL') baseUrl: string, private spinner: NgxSpinnerService, private messageService: MessageService, private datePipe: DatePipe) {
    this.baseUrl = baseUrl;
    this.initFinancialStatusTable();
    this.initStatusTypeDropdown();
    this.initUserSymbolGroupsDropdown();
  }

  initFinancialStatusTable() {
    this.spinner.show();
    this.http.post<any[]>(this.baseUrl + 'FinancialStatus/GetAll', {
      "name": null,
      "type": null,
      "minStatusValue": null,
      "maxStatusValue": null
    }).subscribe(result => {
      this.financialStatuses = result;
      this.spinner.hide();
    }, error => console.error(error));
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

  initStatusTypeDropdown() {
    this.financialStatusTypes = [
      { name: 'Symbol' },
      { name: 'News' },
      { name: 'Author' },
      { name: 'Industry' }
    ];
  }

  removeFilters() {
    this.minStatusValue = null;
    this.maxStatusValue = null;
    this.searchName = null;
    this.selectedFinancialStatusType = null;
    this.selectedUserSymbolGroup = null;
  }

  filterData() {
    this.spinner.show();
    this.http.post<any[]>(this.baseUrl + 'FinancialStatus/GetAll', {
      "name": this.searchName != null ? this.searchName.trim() : null,
      "type": this.selectedFinancialStatusType != null ? this.selectedFinancialStatusType["name"] : null,
      "minStatusValue": this.minStatusValue != null ? this.minStatusValue : null,
      "maxStatusValue": this.maxStatusValue != null ? this.maxStatusValue : null,
      "userSymbolGroupId": this.selectedUserSymbolGroup != null ? this.selectedUserSymbolGroup.id : null,
    }).subscribe(result => {
      this.financialStatuses = result;
      this.spinner.hide();
    }, error => console.error(error));
  }

  isFinancialStatusDataAvailable() {
    return this.financialStatuses != null && this.financialStatuses.length > 0
  }

  financialStatusClick(fs) {
    this.selectedStatus = fs;
    window.open(fs.newsLink, "_blank");
  }
}

