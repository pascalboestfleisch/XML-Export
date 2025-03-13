import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { FileSubmitterComponent } from './file-submitter/file-submitter.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, FileSubmitterComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'xml-loader-frontend';
}
