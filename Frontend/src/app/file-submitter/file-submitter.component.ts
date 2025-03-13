import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { HttpClientModule } from '@angular/common/http';

@Component({
  selector: 'app-file-submitter',
  imports: [HttpClientModule, CommonModule],
  templateUrl: './file-submitter.component.html',
  styleUrls: ['./file-submitter.component.css'],
})
export class FileSubmitterComponent {
  selectedFiles: FileList | null = null;
  parsedQuestions: any[] = [];

  constructor(private http: HttpClient) {}

  onFileSelected(event: any) {
    this.selectedFiles = event.target.files;
  }

  // Endpoint for backend
  uploadFiles() {
    if (!this.selectedFiles || this.selectedFiles.length === 0) {
      console.error('No files selected.');
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < this.selectedFiles.length; i++) {
      formData.append('files', this.selectedFiles[i]);
    }

    this.http
      .post<{ questions: any[] }>('http://localhost:8080/upload/', formData)
      .subscribe({
        next: (response) => {
          console.log('Upload erfolgreich', response);
          this.parsedQuestions = response.questions;
          if (!this.parsedQuestions.length) {
            console.warn('No questions parsed. Check backend.');
          }
        },
        error: (error) => console.error('Fehler beim Upload', error),
      });
  }
}
