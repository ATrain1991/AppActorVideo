import React, { useState, useRef, useEffect } from 'react';
import { Calendar, Settings, Upload, Youtube, RefreshCcw, Eye, EyeOff } from 'lucide-react';
import { DatePicker } from '@/components/ui/calendar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Slider } from '@/components/ui/slider';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/components/ui/use-toast';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// API service for backend communication
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

const api = {
  generateVideo: async (params) => {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('Video generation failed');
    return response.json();
  },
  
  uploadToYoutube: async (videoId, params) => {
    const response = await fetch(`${API_BASE_URL}/youtube/upload/${videoId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!response.ok) throw new Error('YouTube upload failed');
    return response.json();
  },
  
  getVideoStatus: async (videoId) => {
    const response = await fetch(`${API_BASE_URL}/status/${videoId}`);
    if (!response.ok) throw new Error('Failed to get status');
    return response.json();
  }
};

// Custom hooks
const useVideoGeneration = () => {
  const [status, setStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [videoId, setVideoId] = useState(null);

  const generate = async (params) => {
    try {
      setStatus('generating');
      setError(null);
      const { id } = await api.generateVideo(params);
      setVideoId(id);
      
      // Poll for status
      const interval = setInterval(async () => {
        const status = await api.getVideoStatus(id);
        setProgress(status.progress);
        
        if (status.status === 'completed') {
          clearInterval(interval);
          setStatus('completed');
        } else if (status.status === 'failed') {
          clearInterval(interval);
          throw new Error(status.error);
        }
      }, 1000);
      
      return id;
    } catch (err) {
      setError(err.message);
      setStatus('error');
      throw err;
    }
  };

  return { status, progress, error, videoId, generate };
};

// Settings interface
const VideoSettings = ({ settings, onUpdate }) => (
  <Card className="w-full">
    <CardHeader>
      <CardTitle>Video Settings</CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="space-y-2">
        <Label>Video Duration (seconds)</Label>
        <Slider
          value={[settings.duration]}
          onValueChange={(value) => onUpdate({ ...settings, duration: value[0] })}
          min={10}
          max={60}
          step={5}
        />
        <span className="text-sm text-gray-500">{settings.duration} seconds</span>
      </div>

      <div className="space-y-2">
        <Label>Video Quality</Label>
        <Select
          value={settings.quality}
          onValueChange={(value) => onUpdate({ ...settings, quality: value })}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select quality" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Quality</SelectLabel>
              <SelectItem value="1080p">1080p</SelectItem>
              <SelectItem value="720p">720p</SelectItem>
              <SelectItem value="480p">480p</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          checked={settings.includeBackgroundMusic}
          onCheckedChange={(checked) => 
            onUpdate({ ...settings, includeBackgroundMusic: checked })
          }
        />
        <Label>Include Background Music</Label>
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          checked={settings.includeSubtitles}
          onCheckedChange={(checked) =>
            onUpdate({ ...settings, includeSubtitles: checked })
          }
        />
        <Label>Generate Subtitles</Label>
      </div>
    </CardContent>
  </Card>
);

// YouTube settings interface
const YoutubeSettings = ({ settings, onUpdate }) => (
  <Card className="w-full">
    <CardHeader>
      <CardTitle>YouTube Settings</CardTitle>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="space-y-2">
        <Label>Title Template</Label>
        <Input
          value={settings.titleTemplate}
          onChange={(e) => onUpdate({ ...settings, titleTemplate: e.target.value })}
          placeholder="[Actor Name]'s Top Movies"
        />
      </div>

      <div className="space-y-2">
        <Label>Description Template</Label>
        <textarea
          className="w-full min-h-[100px] p-2 border rounded-md"
          value={settings.descriptionTemplate}
          onChange={(e) => onUpdate({ ...settings, descriptionTemplate: e.target.value })}
          placeholder="Check out the best movies featuring [Actor Name]..."
        />
      </div>

      <div className="space-y-2">
        <Label>Tags</Label>
        <Input
          value={settings.tags}
          onChange={(e) => onUpdate({ ...settings, tags: e.target.value })}
          placeholder="movies, actor, top movies (comma separated)"
        />
      </div>

      <div className="flex items-center space-x-2">
        <Switch
          checked={settings.makePublic}
          onCheckedChange={(checked) =>
            onUpdate({ ...settings, makePublic: checked })
          }
        />
        <Label>Make Video Public</Label>
      </div>
    </CardContent>
  </Card>
);

// Main component
export default function VideoGenerator() {
  const [actorName, setActorName] = useState('');
  const [videoType, setVideoType] = useState('most-successful');
  const [generatedVideoUrl, setGeneratedVideoUrl] = useState('');
  const [publishDate, setPublishDate] = useState(null);
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const videoRef = useRef(null);
  const { toast } = useToast();

  const [videoSettings, setVideoSettings] = useState({
    duration: 30,
    quality: '1080p',
    includeBackgroundMusic: true,
    includeSubtitles: false,
  });

  const [youtubeSettings, setYoutubeSettings] = useState({
    titleTemplate: "[Actor Name]'s Movie Journey",
    descriptionTemplate: "Exploring the incredible filmography of [Actor Name]...",
    tags: "movies, actor, film history",
    makePublic: false,
  });

  const { status, progress, error, videoId, generate } = useVideoGeneration();

  const videoTypes = [
    { id: 'most-successful', label: 'Most Successful Movies' },
    { id: 'worst-rated', label: 'Worst Rated Movies' },
    { id: 'best-rated', label: 'Best Rated Movies' },
    { id: 'most-controversial', label: 'Most Controversial Movies' },
    { id: 'chronological', label: 'Chronological Journey' },
    { id: 'award-winning', label: 'Award Winning Performances' },
  ];

  const validateInput = () => {
    const errors = [];
    if (!actorName.trim()) errors.push('Actor name is required');
    if (!videoType) errors.push('Video type must be selected');
    if (videoSettings.duration < 10) errors.push('Video duration must be at least 10 seconds');
    return errors;
  };

  const handleGenerate = async () => {
    const errors = validateInput();
    if (errors.length > 0) {
      toast({
        title: 'Validation Error',
        description: errors.join('\n'),
        variant: 'destructive',
      });
      return;
    }

    try {
      const params = {
        actorName,
        videoType,
        settings: videoSettings,
      };
      
      await generate(params);
      setGeneratedVideoUrl(`${API_BASE_URL}/videos/${videoId}`);
      
      toast({
        title: 'Success!',
        description: 'Video generated successfully',
      });
    } catch (err) {
      toast({
        title: 'Error',
        description: err.message,
        variant: 'destructive',
      });
    }
  };

  const handleUpload = async () => {
    if (!generatedVideoUrl || !publishDate) {
      toast({
        title: 'Error',
        description: 'Please generate a video and select a publish date first',
        variant: 'destructive',
      });
      return;
    }

    try {
      const params = {
        ...youtubeSettings,
        publishDate: publishDate.toISOString(),
        title: youtubeSettings.titleTemplate.replace('[Actor Name]', actorName),
        description: youtubeSettings.descriptionTemplate.replace('[Actor Name]', actorName),
      };

      await api.uploadToYoutube(videoId, params);
      
      toast({
        title: 'Success!',
        description: 'Video scheduled for upload successfully',
      });
    } catch (err) {
      toast({
        title: 'Upload Error',
        description: err.message,
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Movie Shorts Generator</h1>
        <Button
          variant="outline"
          size="icon"
          onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="space-y-6">
          {/* Basic Settings */}
          <Card>
            <CardContent className="pt-6 space-y-4">
              {/* Actor Input */}
              <div className="space-y-2">
                <Label htmlFor="actor-name">Actor Name</Label>
                <Input
                  id="actor-name"
                  value={actorName}
                  onChange={(e) => setActorName(e.target.value)}
                  placeholder="Enter actor name"
                />
              </div>

              {/* Video Type Selection */}
              <div className="space-y-2">
                <Label>Video Type</Label>
                <RadioGroup
                  value={videoType}
                  onValueChange={setVideoType}
                  className="space-y-2"
                >
                  {videoTypes.map((type) => (
                    <div key={type.id} className="flex items-center space-x-2">
                      <RadioGroupItem value={type.id} id={type.id} />
                      <Label htmlFor={type.id}>{type.label}</Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            </CardContent>
          </Card>

          {/* Advanced Settings */}
          {showAdvancedSettings && (
            <Accordion type="single" collapsible>
              <AccordionItem value="video-settings">
                <AccordionTrigger>Video Settings</AccordionTrigger>
                <AccordionContent>
                  <VideoSettings
                    settings={videoSettings}
                    onUpdate={setVideoSettings}
                  />
                </AccordionContent>
              </AccordionItem>

              <AccordionItem value="youtube-settings">
                <AccordionTrigger>YouTube Settings</AccordionTrigger>
                <AccordionContent>
                  <YoutubeSettings
                    settings={youtubeSettings}
                    onUpdate={setYoutubeSettings}
                  />
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}

          {/* Generate Button */}
          <Button 
            onClick={handleGenerate}
            disabled={status === 'generating'}
            className="w-full"
          >
            {status === 'generating' ? (
              <>
                <RefreshCcw className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate Video'
            )}
          </Button>
        </div>

        <div className="space-y-6">
          {/* Progress and Preview */}
          {status === 'generating' && (
            <Card>
              <CardContent className="pt-6 space-y-4">
                <Progress value={progress} />
                <p className="text-sm text-gray-500">
                  Generating video... {progress}%
                </p>
              </CardContent>
            </Card>
          )}

          {/* Generated Video Preview */}
          {generatedVideoUrl && (
            <Card>
              <CardHeader>
                <CardTitle>Preview</CardTitle>
              </CardHeader>
              <CardContent>
                <video
                  ref={videoRef}
                  controls
                  className="w-full aspect-video bg-gray-100 rounded-lg"
                  src={generatedVideoUrl}
                />
              </CardContent>
            </Card>
          )}

          {/* Publishing Section */}
          {generatedVideoUrl && (
            <Card>
              <CardHeader>
                <CardTitle>Publish to YouTube</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Publish Date</Label>
                  <DatePicker
                    selected={publishDate}
                    onSelect={setPublishDate}
                    disabled={(date) => date < new Date()}
                  />
                </div>
                <Button onClick={handleUpload} className="w-full">
                  <Youtube className="mr-2 h-4 w-4" />
                  Schedule Upload
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
      