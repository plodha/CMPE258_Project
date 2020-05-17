import { Component, OnInit } from '@angular/core';
import { FormGroup, FormControl, Validators, FormBuilder } from '@angular/forms';
import {ApiService} from '../api.service';

@Component({
  selector: 'app-video-form',
  templateUrl: './video-input-form.component.html',
  styleUrls: ['./video-input-form.component.css']
})
export class VideoInputFormComponent implements OnInit {
  videoFileForm: FormGroup;
   submitted = false;
   url = '';
  loading = false;
  output_file = '';
  textfileZip = '';
  isDisabled = true;
  error = ''
  determinateValue = 50
  classification = ''
  title = ''
  receipes = []
  ingrs = ''
  calorie = ''
  calories = []




  private time: string;

  ngOnInit(): void {
    const video = document.getElementById('video');

    this.videoFileForm = new FormGroup({

      file1 : new FormControl('')
    });
  }

  constructor(private apiService: ApiService) { }
  get f() { return this.videoFileForm.controls; }


  onSubmit() {
    this.submitted = true;
    this.loading = true;

    const formData = new FormData();
    formData.append('file', this.videoFileForm.get('file1').value);


    var api = this.apiService
    var obj = this
  //  var labelElement = document.getElementById('statusLabel')
  /*  if (this.loading == true) {
      var statusUpdate = setInterval(function () {
        console.log(api)
        api.getStatus().subscribe((data: any) => {
          console.log(data.label)
          console.log(data.percent)
          labelElement.innerHTML = '<h4>' + data.label + '</h4>'
          obj.determinateValue = data.percent

        });

      }, 1000);
    }*/

    const all = this.apiService.createNewRequest(formData).subscribe((data: any) => {
      console.log('Call completed ')
      console.log(data);
      this.loading = false;
      this.classification = data.classification
      var c = data.calorie[0];
      c  = c.replace("{","");
      c = c.replace("}","");
      this.calories = c.split(",");

      this.calorie = c;
      var ingrs = data.receipe.ingrs;
      var i;
      var text = '';
      for (i = 0; i < ingrs.length; i++) {
        text += ingrs[i] + ",";
      }

      this.ingrs = text

        this.title = data.receipe.title
        this.receipes = data.receipe.recipe

        document.getElementById('result').style.display = 'block';

    });


  }

  onSelectFile(event) {
    if (event.target.files && event.target.files[0]) {
      const reader = new FileReader();

      const file = event.target.files[0];
      console.log(file)
      this.videoFileForm.get('file1').setValue(file);
      reader.readAsDataURL(file); // read file as data url


      reader.onload = (_event) => { // called once readAsDataURL is completed
        this.url = reader.result as string;
        console.log('url : ', this.url);
          document.getElementById('result').style.display = 'none';

        //const audioPlayer = <HTMLMediaElement>document.getElementById('image');
      //  audioPlayer.load();
       // audioPlayer.play();
      };

    }
  }



}
