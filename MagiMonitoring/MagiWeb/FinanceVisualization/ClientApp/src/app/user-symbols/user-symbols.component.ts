import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { MessageService, ConfirmationService } from 'primeng/api';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-user-symbols',
  templateUrl: './user-symbols.component.html'
})
export class UserSymbolsComponent {
  baseUrl: string;
  userSymbolGroupDialog = false;
  currentUserSymbolGroup: UserSymbolGroup;

  distinctSymbolsList: any[] = [];
  selectedSymbols: any[] = [];

  userSymbolGroups: UserSymbolGroup[];
  selectedUserSymbolGroups: any[] = [];

  constructor(private http: HttpClient,
    @Inject('BASE_URL') baseUrl: string,
    private spinner: NgxSpinnerService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService) {
    this.baseUrl = baseUrl;
    this.initDistinctSymbolsDropdown();
    this.initUserSymbolGroupDataTable();
  }

  initDistinctSymbolsDropdown() {
    this.spinner.show();
    this.http.get<any[]>(this.baseUrl + 'SectorsIndustries/GetDistinctFirmSymbols').subscribe(result => {
      this.distinctSymbolsList = [];
      result.forEach(item => {
        this.distinctSymbolsList.push({
          name: item.symbol,
          fullName: item.name + "- " + item.symbol
        });
      });
      this.spinner.hide();
    }, error => console.error(error));
  }

  initUserSymbolGroupDataTable() {
    this.spinner.show();
    this.http.get<UserSymbolGroup[]>(this.baseUrl + 'UserSymbolGroup/GetUserSymbolGroups').subscribe(result => {
      this.userSymbolGroups = result;
      this.spinner.hide();
    }, error => console.error(error));
  }

  openNew() {
    this.currentUserSymbolGroup = {
      Id: 0,
      InsertDate: "",
      Name: "",
      UserSymbolGroupDetails: []
    };
    this.selectedSymbols = [];
    this.userSymbolGroupDialog = true;
  }

  deleteUserSymbolGroup(usg: any) {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete ' + usg.name + 'group ?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.spinner.show();
        this.http.post<any>(this.baseUrl + 'UserSymbolGroup/DeleteUserSymbolGroups', {
          "ids": [usg.id],
        }).subscribe(result => {
          this.spinner.hide();
          this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'User Symbol Groups deleted', life: 3000 });
          this.hideDialog();
          this.initUserSymbolGroupDataTable();
        }, error => console.error(error));
        this.currentUserSymbolGroup = {
          Id: 0,
          InsertDate: "",
          Name: "",
          UserSymbolGroupDetails: []
        };
      }
    });
  }

  hideDialog() {
    this.userSymbolGroupDialog = false;
  }

  saveUserSymbolGroup() {
    if (this.currentUserSymbolGroup.Name.trim() === "") {
      this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: 'User Symbol Group Name cannot be empty or white space.', life: 3000 });
      return;
    } else if (this.selectedSymbols.length == 0) {
      this.messageService.add({ key: 'trToast', severity: 'error', summary: 'Error', detail: 'At least one symbol must be selected.', life: 3000 });
      return;
    }
    this.selectedSymbols.forEach(ss => {
      this.currentUserSymbolGroup.UserSymbolGroupDetails.push(ss["name"]);
    });

    this.spinner.show();
    this.http.post<any>(this.baseUrl + 'UserSymbolGroup/PostUserSymbolGroup', {
      "name": this.currentUserSymbolGroup.Name,
      "newUserSymbolGroupDetails": this.selectedSymbols.map(function (a) { return { "symbol": a["name"] }; }),
    }).subscribe(result => {
      this.spinner.hide();
      this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'New User Symbol Group created', life: 3000 });
      this.hideDialog();
      this.initUserSymbolGroupDataTable();
    }, error => console.error(error));
  }

  symbolGroupListToString(userSymbolGroupDetails: UserSymbolGroupDetail[]) {
    return userSymbolGroupDetails.map(function (a) { return a["symbol"]; }).join(", ");
  }

  deleteSelectedUserSymbolGroups() {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete the selected user symbol groups?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.spinner.show();
        this.http.post<any>(this.baseUrl + 'UserSymbolGroup/DeleteUserSymbolGroups', {
          "ids": this.selectedUserSymbolGroups.map(function (a) { return a["id"]; }),
        }).subscribe(result => {
          this.selectedUserSymbolGroups = [];
          this.spinner.hide();
          this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'Selected User Symbol Groups deleted', life: 3000 });
          this.hideDialog();
          this.initUserSymbolGroupDataTable();
        }, error => console.error(error));
      }
    });
  }
}

interface UserSymbolGroupDetail {
  Id: number,
  Symbol: string,
  UserSymbolGroupId: number
}

interface UserSymbolGroup {
  Id: number,
  Name: string,
  InsertDate: string,
  UserSymbolGroupDetails: UserSymbolGroupDetail[]
}
