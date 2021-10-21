import { Component, Inject, OnInit, ViewChild } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { NgxSpinnerService } from 'ngx-spinner';
import { MessageService, ConfirmationService } from 'primeng/api';
import { Router } from '@angular/router';

@Component({
  selector: 'app-user-management',
  templateUrl: './user-management.component.html',
  styles: [`
.status-badge-false {
              border-radius: 2px;
              padding: .25em .5rem;
              text-transform: uppercase;
              font-weight: 700;
              font-size: 12px;
              background-color: #FFCDD2;
              color: #C63737;
              letter-spacing: .3px;}

.status-badge-true {
              border-radius: 2px;
              padding: .25em .5rem;
              text-transform: uppercase;
              font-weight: 700;
              font-size: 12px;
              background-color: #C8E6C9;
              color: #256029;
              letter-spacing: .3px;}`]
})
export class UserManagementComponent {
  users: any[];
  baseUrl: string;
  isRegistrationOpen = true;

  constructor(private http: HttpClient,
    @Inject('BASE_URL') baseUrl: string,
    private spinner: NgxSpinnerService,
    private confirmationService: ConfirmationService,
    private messageService: MessageService,
    private router: Router) {
    this.baseUrl = baseUrl;
    this.checkIsAuthenticated();
    this.filterData();
  }

  async checkIsAuthenticated() {
    this.spinner.show();
    let result = await this.http.get<any>(this.baseUrl + 'UserManagement/IsAuthenticated').toPromise();
    if (!result) {
      this.messageService.add({ key: 'trToast', severity: 'warn', summary: 'Not Authorized', detail: 'You are not authorized to view the page. Redirected to main page.', life: 3000 });
      this.router.navigate(['']);
    }
    else {
      this.isRegistrationOpen = await this.http.get<any>(this.baseUrl + 'UserManagement/GetRegistrationStatus').toPromise();
    }
    this.spinner.hide();
  }

  statusChanged(event) {
    this.spinner.show();
    let result = this.http.post<any>(this.baseUrl + 'UserManagement/UpdateRegistrationStatus', {
      "status": this.isRegistrationOpen
    }).toPromise();

    this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'Registration status updated', life: 3000 });
    this.isRegistrationOpen = !!result;
    this.spinner.hide();
  }

  filterData() {
    this.spinner.show();
    this.http.post<any[]>(this.baseUrl + 'UserManagement/GetAll', {

    }).subscribe(result => {
      this.users = result;
      this.spinner.hide();
    }, error => console.error(error));
  }

  isFinancialStatusDataAvailable() {
    return this.users != null && this.users.length > 0
  }

  deleteUserClick(userId) {
    this.confirmationService.confirm({
      message: 'Are you sure you want to delete the user?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.spinner.show();
        this.http.post<any>(this.baseUrl + 'UserManagement/DeleteUser', {
          "id": userId,
        }).subscribe(result => {
          this.spinner.hide();
          this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'User deleted', life: 3000 });
          this.filterData();
        }, error => console.error(error));
      }
    });
  }

  updateManualNewsPermission(userId) {
    this.confirmationService.confirm({
      message: 'Are you sure you want to toggle the permission for adding manual news for the user?',
      header: 'Confirm',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.spinner.show();
        this.http.post<any>(this.baseUrl + 'UserManagement/UpdateUserManualNewsPermission', {
          "id": userId,
        }).subscribe(result => {
          this.spinner.hide();
          this.messageService.add({ key: 'trToast', severity: 'success', summary: 'Successful', detail: 'User manual news adding permission updated.', life: 3000 });
          this.filterData();
        }, error => console.error(error));
      }
    });
  }
}

