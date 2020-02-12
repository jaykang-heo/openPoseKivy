from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
import cv2
from kivy.uix.popup import Popup
import os
import socket
import sys
import pickle
import struct

class CamApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.img1=Image()
        menubar = GridLayout(cols=3, size_hint=(1,None))
        screenbox = BoxLayout(height=400)
        openb = Button(text="Open File", size_hint=(0.3, None), on_release=self.open_pop_up)
        self.paused = Button(text="pause", size_hint=(0.3, None), on_release=self.pause)
        stop = Button(text="stop", size_hint=(0.3, None), on_release=self.stop)
        menubar.add_widget(openb)
        menubar.add_widget(self.paused)
        menubar.add_widget(stop)
        self.layout.add_widget(menubar)
        screenbox.add_widget(self.img1)
        self.layout.add_widget(screenbox)
        self.slider = Slider(min=0, max=0, height=30)
        self.slider.size_hint = (1, None)
        self.slider.bind(value=self.on_frame_change)
        self.clock = Clock
        self.layout.add_widget(self.slider)

        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clientsocket.connect(('localhost', 8089))
        return self.layout

    def open_pop_up(self, button):
        layout = BoxLayout(orientation='vertical')
        # open button
        filechooser = FileChooserListView(path=os.getcwd())
        filechooser.bind(on_selection=lambda x: self.selected(filechooser.selection))
        popup_menubar = GridLayout(cols=2, size_hint=(1,None))

        open_btn = Button(text='open', size_hint=(0.5, None))
        open_btn.bind(on_release=lambda x: self.open(filechooser.path, filechooser.selection))
        self.popup = Popup(title='Demo Popup',
                      content=layout)
        self.popup.open()
        closebtn = Button(text='close', on_press=self.close, size_hint=(0.5, None))

        popup_menubar.add_widget(open_btn)
        popup_menubar.add_widget(closebtn)
        layout.add_widget(filechooser)
        layout.add_widget(popup_menubar)

    def close(self):
        self.popup.dismiss()

    def pause(self, button):
        try:
            if self.paused.text == 'pause':
                self.clock.unschedule(self.update)
                self.paused.text = 'play'
            else:
                self.clock.schedule_interval(self.update, 1.0 / self.total_frame)
                self.paused.text = 'pause'
        except:
            pass

    def stop(self, button):
        self.clock.unschedule(self.update)

    def open(self, path, filename):
        self.clock.unschedule(self.update)

        self.cap = cv2.VideoCapture(filename[0])
        self.total_frame = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.slider.max = int(self.total_frame)
        self.clock.schedule_interval(self.update, 1.0 / self.total_frame)
        self.data = list()
        self.popup.dismiss()

    def selected(self, filename):
        print("selected: %s" % filename[0])

    def on_frame_change(self, instance, value):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, value)

    def update(self, dt):
            ret, frame = self.cap.read()
            if ret and len(self.data) < self.total_frame:

                # Serialize frame
                data = pickle.dumps(frame)
                # Send message length first
                message_size = struct.pack("L", len(data))
                # Then data
                self.clientsocket.sendall(message_size + data)

                self.data.append(frame)
                # convert to kivy format
                buf1 = cv2.flip(frame, 0)
                buf = buf1.tostring()
                texture1 = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
                texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
                self.img1.texture = texture1

                # move the slider
                # print(len(self.data), " / ", self.total_frame)
                self.slider.value = len(self.data)


if __name__ == '__main__':
    CamApp().run()
