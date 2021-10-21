import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { TabViewModule } from 'primeng/tabview';
import { TableModule } from 'primeng/table';
import { ChartModule } from 'primeng/chart';
import { ToastModule } from 'primeng/toast';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { InputTextModule } from 'primeng/inputtext';
import { ApiAuthorizationModule } from 'src/api-authorization/api-authorization.module';
import { NgxSpinnerModule, NgxSpinnerService } from "ngx-spinner";
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { DialogModule } from 'primeng/dialog';
import { FieldsetModule } from 'primeng/fieldset';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { MultiSelectModule } from 'primeng/multiselect';
import { InputNumberModule } from 'primeng/inputnumber';
import { ToolbarModule } from 'primeng/toolbar';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { TooltipModule } from 'primeng/tooltip';
import { PlotlyViaCDNModule } from 'angular-plotly.js';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { ToggleButtonModule } from 'primeng/togglebutton';
import { JoyrideModule } from 'ngx-joyride';
import { AngularEditorModule } from '@kolkov/angular-editor';
import { NgcCookieConsentModule, NgcCookieConsentConfig } from 'ngx-cookieconsent';

PlotlyViaCDNModule.plotlyVersion = "1.54.0";
const cookieConfig: NgcCookieConsentConfig = {
  "cookie": {
    "domain": "magifinance.com"
  },
  "position": "bottom-right",
  "theme": "classic",
  "palette": {
    "popup": {
      "background": "#000000",
      "text": "#ffffff",
      "link": "#ffffff"
    },
    "button": {
      "background": "#f1d600",
      "text": "#000000",
      "border": "transparent"
    }
  },
  "type": "info",
  "content": {
    "message": "This website uses cookies to ensure you get the best experience on our website.",
    "dismiss": "Got it!",
    "deny": "Refuse cookies",
    "link": "",
    "href": ""
  }
}

import { AppComponent } from './app.component';
import { NavMenuComponent } from './nav-menu/nav-menu.component';
import { HomeComponent } from './home/home.component';
import { FinanceNewsComponent } from './finance-news/finance-news.component';

import { AuthorizeGuard } from 'src/api-authorization/authorize.guard';
import { AuthorizeInterceptor } from 'src/api-authorization/authorize.interceptor';
import { ScrollDispatcher } from '@angular/cdk/scrolling';
import { Platform } from '@angular/cdk/platform';
import { MessageService, ConfirmationService } from 'primeng/api';
import { DatePipe, DecimalPipe } from '@angular/common';
import { UserSymbolsComponent } from './user-symbols/user-symbols.component';
import { PredictionsComponent } from './predictions/predictions.component';
import { FinancialStatusComponent } from './financial-status/financial-status.component';
import { CorrelationsComponent } from './correlations/correlations.component';
import { UserManagementComponent } from './user-management/user-management.component';
import { ManualNewsComponent } from './manual-news/manual-news.component';
import { OtherNewsTopicsComponent } from './other-news-topics/other-news-topics.component';


@NgModule({
  declarations: [
    AppComponent,
    NavMenuComponent,
    HomeComponent,
    FinanceNewsComponent,
    UserSymbolsComponent,
    PredictionsComponent,
    FinancialStatusComponent,
    CorrelationsComponent,
    UserManagementComponent,
    ManualNewsComponent,
    OtherNewsTopicsComponent
  ],
  imports: [
    BrowserModule.withServerTransition({ appId: 'ng-cli-universal' }),
    HttpClientModule,
    FormsModule,
    ApiAuthorizationModule,
    RouterModule.forRoot([
      { path: '', component: HomeComponent, pathMatch: 'full' },
//       { path: 'finance-news', component: FinanceNewsComponent, canActivate: [AuthorizeGuard] },
      { path: 'finance-news', component: FinanceNewsComponent },
      { path: 'user-symbols', component: UserSymbolsComponent, canActivate: [AuthorizeGuard] },
      { path: 'predictions', component: PredictionsComponent, canActivate: [AuthorizeGuard] },
      { path: 'financial-status', component: FinancialStatusComponent, canActivate: [AuthorizeGuard] },
      { path: 'correlations', component: CorrelationsComponent, canActivate: [AuthorizeGuard] },
      { path: 'user-management', component: UserManagementComponent, canActivate: [AuthorizeGuard] },
      { path: 'add-other-news', component: ManualNewsComponent, canActivate: [AuthorizeGuard] },
      { path: 'other-news-topics', component: OtherNewsTopicsComponent, canActivate: [AuthorizeGuard] }

    ]),
    TableModule,
    BrowserAnimationsModule,
    InputTextModule,
    CardModule,
    ButtonModule,
    ScrollingModule,
    TabViewModule,
    NgxSpinnerModule,
    ChartModule,
    ToastModule,
    DropdownModule,
    CalendarModule,
    DialogModule,
    FieldsetModule,
    ScrollPanelModule,
    MultiSelectModule,
    InputNumberModule,
    ToolbarModule,
    ConfirmDialogModule,
    TooltipModule,
    PlotlyViaCDNModule,
    InputTextareaModule,
    ToggleButtonModule,
    JoyrideModule.forRoot(),
    AngularEditorModule,
    NgcCookieConsentModule.forRoot(cookieConfig)
  ],
  providers: [
    { provide: HTTP_INTERCEPTORS, useClass: AuthorizeInterceptor, multi: true },
    ScrollDispatcher,
    Platform,
    NgxSpinnerService,
    AuthorizeGuard,
    MessageService,
    DatePipe,
    DecimalPipe,
    ConfirmationService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
