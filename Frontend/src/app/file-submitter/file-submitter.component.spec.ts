import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FileSubmitterComponent } from './file-submitter.component';

describe('FileSubmitterComponent', () => {
  let component: FileSubmitterComponent;
  let fixture: ComponentFixture<FileSubmitterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FileSubmitterComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FileSubmitterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
