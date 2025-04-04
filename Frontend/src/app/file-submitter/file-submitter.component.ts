import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { HttpClientModule } from '@angular/common/http';
import { MatExpansionModule } from '@angular/material/expansion';
import { FormsModule } from '@angular/forms';
import { MatListModule } from '@angular/material/list';
import { MatCheckboxModule } from '@angular/material/checkbox';

@Component({
  selector: 'app-file-submitter',
  imports: [
    HttpClientModule,
    CommonModule,
    MatExpansionModule,
    FormsModule,
    MatListModule,
    MatCheckboxModule,
  ],
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
          console.log('Upload successfull', response);
          this.parsedQuestions = response.questions;
          if (!this.parsedQuestions.length) {
            console.warn('No questions parsed, check backend.');
          }
        },
        error: (error) => console.error('Error during upload', error),
      });
  }

  // Export-Function for selected questions
  exportSelectedQuestions() {
    const selectedQuestions = this.parsedQuestions.filter((q) => {

      const isMainQuestionSelected = q.selected;
      const areSubquestionsSelected = q.subquestions?.some((sub: { selected: any }) => sub.selected);
      
      return (isMainQuestionSelected || areSubquestionsSelected);
    });
  
    if (selectedQuestions.length === 0) {
      console.warn('No questions selected for export.');
      return;
    }
  
    this.http
      .post(
        'http://localhost:8080/export/',
        { questions: selectedQuestions },
        { responseType: 'blob' }
      )
      .subscribe((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'exported_questions.xml';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      });
  }
}
