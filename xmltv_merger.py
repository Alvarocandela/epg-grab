#!/usr/bin/env python3
"""
XMLTV Merger - Merges multiple XMLTV files and filters channels based on a specification file.

This program takes multiple XMLTV format files and creates a single merged file containing
only the channels specified in a separate configuration file. It can also download EPG files
from remote URLs before processing.
"""

import xml.etree.ElementTree as ET
import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
import urllib.request
import urllib.error
import gzip
import shutil
import os


class XMLTVMerger:
    def __init__(self):
        self.channels = {}  # Store channels by ID
        self.programmes = []  # Store all programmes
        self.channel_filter = set()  # Channels to include
        self.channel_config = {}  # Advanced channel configuration
        self.use_advanced_config = False  # Whether to use advanced configuration
        self.channel_id_mapping = {}  # Maps original channel IDs to new ones
        self.sources_config = {}  # Source file download configuration
        self.requested_channels = {}  # Tracks requested channels by source file
        self.found_channels = {}  # Tracks found channels by source file
        
        # Genre mapping for TVHeadend compatibility - Multilingual support
        self.genre_mapping = {
            # Spanish to English genre mappings
            # Information/News categories
            'Información/Informativo': 'News',
            'Información/Reportaje': 'Documentary', 
            'Información/Documental': 'Documentary',
            'Información/Magazine': 'News Magazine',
            'Información/Deportivo': 'Sports',
            'Información/Meteorología': 'Weather',
            'Información/Política': 'Politics',
            
            # Entertainment categories
            'Entretenimiento/Corazon y sociedad': 'Talk Show',
            'Entretenimiento/Humor': 'Comedy',
            'Entretenimiento/Variedades': 'Entertainment',
            'Entretenimiento/Concurso': 'Game Show',
            'Entretenimiento/Reality show': 'Reality',
            'Entretenimiento/Musical': 'Music',
            
            # Cinema/Movies
            'Cine/Película': 'Movie',
            'Cine/Drama': 'Drama',
            'Cine/Comedia': 'Comedy',
            'Cine/Acción': 'Action',
            'Cine/Thriller': 'Thriller',
            'Cine/Terror': 'Horror',
            'Cine/Aventuras': 'Adventure',
            'Cine/Ciencia ficción': 'Science Fiction',
            'Cine/Romance': 'Romance',
            'Cine/Western': 'Western',
            'Cine/Bélico': 'War',
            'Cine/Histórico': 'Historical',
            'Cine/Comedia romántica': 'Romantic Comedy',
            
            # Sports
            'Deportes': 'Sports',
            'Deportes/Fútbol': 'Sports',
            'Deportes/Motor': 'Motorsport',
            'Deportes/Baloncesto': 'Sports',
            'Deportes/Tenis': 'Sports',
            'Deportes/Ciclismo': 'Sports',
            
            # Children's content
            'Infantil/Dibujos animados': 'Animation',
            'Infantil/Juvenil': 'Children',
            'Infantil/Educativo': 'Educational',
            
            # Cultural/Educational
            'Cultura/Arte': 'Arts',
            'Cultura/Historia': 'Documentary',
            'Cultura/Ciencia': 'Science',
            'Cultura/Naturaleza': 'Nature',
            'Cultura/Religioso': 'Religious',
            
            # Series/Fiction
            'Serie/Drama': 'Drama',
            'Serie/Comedia': 'Comedy',
            'Serie/Policiaca': 'Crime',
            'Serie/Acción': 'Action',
            'Serie/Ciencia ficción': 'Science Fiction',
            'Serie/Thriller': 'Thriller',
            
            # Lifestyle
            'Ocio y Aficiones/Viajes': 'Travel',
            'Ocio y Aficiones/Gastronomía': 'Food',
            'Ocio y Aficiones/Decoración': 'Lifestyle',
            'Ocio y Aficiones/Motor': 'Automotive',
            'Ocio y Aficiones/Naturaleza': 'Nature',
            'Ocio y Aficiones/Juegos': 'Game Show',
            
            # Music and Arts
            'Música': 'Music',
            'Música/Pop-Rock': 'Music',
            'Música/Clásica': 'Classical Music',
            'Música/Jazz': 'Music',
            'Teatro': 'Performing Arts',
            'Danza': 'Performing Arts',
            'Opera': 'Performing Arts',
            
            # Other common Spanish genres
            'Telenovela': 'Soap Opera',
            'Magacín': 'Magazine',
            'Debate': 'Talk Show',
            'Educativo': 'Educational',
            'Religioso': 'Religious',
            'Erótico': 'Adult',
            
            # Handle slash variations (both directions)
            'Viajes': 'Travel',
            'Reportaje': 'Documentary',
            'Informativo': 'News',
            'Corazón y sociedad': 'Talk Show',
            'Humor': 'Comedy',
            'Variedades': 'Entertainment',
            'Concurso': 'Game Show',
            'Reality show': 'Reality',
            'Musical': 'Music',
            'Película': 'Movie',
            'Drama': 'Drama',
            'Comedia': 'Comedy',
            'Acción': 'Action',
            'Thriller': 'Thriller',
            'Terror': 'Horror',
            'Aventuras': 'Adventure',
            'Ciencia ficción': 'Science Fiction',
            'Romance': 'Romance',
            'Western': 'Western',
            'Bélico': 'War',
            'Histórico': 'Historical',
            'Fútbol': 'Sports',
            'Motor': 'Motorsport',
            'Baloncesto': 'Sports',
            'Tenis': 'Sports',
            'Ciclismo': 'Sports',
            'Dibujos animados': 'Animation',
            'Juvenil': 'Children',
            'Arte': 'Arts',
            'Historia': 'Documentary',
            'Ciencia': 'Science',
            'Naturaleza': 'Nature',
            'Policiaca': 'Crime',
            'Gastronomía': 'Food',
            'Decoración': 'Lifestyle',
            
            # Additional mappings found in Spanish EPG
            'Entretenimiento': 'Entertainment',
            'Series/Policíaca': 'Crime',
            'Ocio y Aficiones/Cocina': 'Food',
            'Documental/Otros': 'Documentary',
            'Serie/Telenovela': 'Soap Opera',
            'Cocina': 'Food',
            'Otros': 'Other',
            
            # German genre mappings
            'Krimi': 'Crime',
            'Krimiserie': 'Crime',
            'Kriminalfilm': 'Crime',
            'Abenteuer': 'Adventure',
            'Action': 'Action',
            'Actionfilm': 'Action',
            'Actionkomödie': 'Action',
            'Actionserie': 'Action',
            'Actionthriller': 'Action',
            'Animation': 'Animation',
            'Animationsfilm': 'Animation',
            'Animationsserie': 'Animation',
            'Aktuelles': 'News',
            'Nachrichten': 'News',
            'Dokumentation': 'Documentary',
            'Dokufilm': 'Documentary',
            'Dokuserie': 'Documentary',
            'Dokumentarfilm': 'Documentary',
            'Komödie': 'Comedy',
            'Komödienfilm': 'Comedy',
            'Komödienserie': 'Comedy',
            'Drama': 'Drama',
            'Dramafilm': 'Drama',
            'Dramaserie': 'Drama',
            'Thriller': 'Thriller',
            'Psychothriller': 'Thriller',
            'Thrillerserie': 'Thriller',
            'Horror': 'Horror',
            'Horrorfilm': 'Horror',
            'Horrorserie': 'Horror',
            'Science Fiction': 'Science Fiction',
            'Science-Fiction': 'Science Fiction',
            'Sci-Fi': 'Science Fiction',
            'Fantasy': 'Fantasy',
            'Fantasyfilm': 'Fantasy',
            'Fantasyserie': 'Fantasy',
            'Romantik': 'Romance',
            'Liebesfilm': 'Romance',
            'Liebesdrama': 'Romance',
            'Western': 'Western',
            'Westernfilm': 'Western',
            'Westernserie': 'Western',
            'Kriegsfilm': 'War',
            'Kriegsdrama': 'War',
            'Historienfilm': 'Historical',
            'Sport': 'Sports',
            'Sportsendung': 'Sports',
            'Fußball': 'Sports',
            'Motorsport': 'Motorsport',
            'Autorennen': 'Motorsport',
            'Musik': 'Music',
            'Musiksendung': 'Music',
            'Musikfilm': 'Music',
            'Konzert': 'Music',
            'Kindersendung': 'Children',
            'Kinderfilm': 'Children',
            'Kinderserie': 'Children',
            'Jugendserie': 'Children',
            'Jugendfilm': 'Children',
            'Bildung': 'Educational',
            'Bildungsprogramm': 'Educational',
            'Wissenschaft': 'Science',
            'Natur': 'Nature',
            'Naturdokumentation': 'Nature',
            'Tierdokumentation': 'Nature',
            'Reise': 'Travel',
            'Reisebericht': 'Travel',
            'Reisedokumentation': 'Travel',
            'Kochsendung': 'Food',
            'Kochen': 'Food',
            'Lifestyle': 'Lifestyle',
            'Magazine': 'Magazine',
            'Magazin': 'Magazine',
            'Talk': 'Talk Show',
            'Talkshow': 'Talk Show',
            'Show': 'Entertainment',
            'Unterhaltung': 'Entertainment',
            'Quiz': 'Game Show',
            'Gameshow': 'Game Show',
            'Reality-TV': 'Reality',
            'Reality': 'Reality',
            'Soap': 'Soap Opera',
            'Seifenoper': 'Soap Opera',
            'Telenovela': 'Soap Opera',
            
            # Italian genre mappings
            'Animazione': 'Animation',
            'Cartoni Animati': 'Animation',
            'Anime': 'Animation',
            'Azione': 'Action',
            'Avventura': 'Adventure',
            'Commedia': 'Comedy',
            'Drammatico': 'Drama',
            'Dramma': 'Drama',
            'Thriller': 'Thriller',
            'Horror': 'Horror',
            'Fantascienza': 'Science Fiction',
            'Fantasy': 'Fantasy',
            'Romantico': 'Romance',
            'Western': 'Western',
            'Guerra': 'War',
            'Storico': 'Historical',
            'Poliziesco': 'Crime',
            'Giallo': 'Crime',
            'Documentario': 'Documentary',
            'Notizie': 'News',
            'Attualità': 'News',
            'Sport': 'Sports',
            'Calcio': 'Sports',
            'Motori': 'Motorsport',
            'Musica': 'Music',
            'Ragazzi e Musica': 'Children',
            'Bambini': 'Children',
            'Educativo': 'Educational',
            'Scienza': 'Science',
            'Natura': 'Nature',
            'Viaggi': 'Travel',
            'Cucina': 'Food',
            'Lifestyle': 'Lifestyle',
            'Magazine': 'Magazine',
            'Talk Show': 'Talk Show',
            'Spettacolo': 'Entertainment',
            'Intrattenimento': 'Entertainment',
            'Quiz': 'Game Show',
            'Reality': 'Reality',
            'Soap Opera': 'Soap Opera',
            'Telenovela': 'Soap Opera',
            'Serie TV': 'Series',
            'Film': 'Movie',
            'Altri Programmi': 'Other',
            'Altri': 'Other',
            'Altro': 'Other',
            'Giochi': 'Game Show',
            'Mondo e Tendenze': 'Entertainment',
            
            # Dutch genre mappings
            'Actie': 'Action',
            'Actiekomedie': 'Action',
            'Actieserie': 'Action',
            'Avontuur': 'Adventure',
            'Komedie': 'Comedy',
            'Drama': 'Drama',
            'Thriller': 'Thriller',
            'Horror': 'Horror',
            'Science Fiction': 'Science Fiction',
            'Fantasy': 'Fantasy',
            'Romantiek': 'Romance',
            'Western': 'Western',
            'Oorlog': 'War',
            'Historisch': 'Historical',
            'Misdaad': 'Crime',
            'Documentaire': 'Documentary',
            'Nieuws': 'News',
            'Actualiteiten': 'News',
            'Sport': 'Sports',
            'Voetbal': 'Sports',
            'Motorsport': 'Motorsport',
            'Muziek': 'Music',
            'Kinderen': 'Children',
            'Jeugd': 'Children',
            'Animatie': 'Animation',
            'Animatieserie': 'Animation',
            'Educatief': 'Educational',
            'Wetenschap': 'Science',
            'Natuur': 'Nature',
            'Reizen': 'Travel',
            'Koken': 'Food',
            'Lifestyle': 'Lifestyle',
            'Magazine': 'Magazine',
            'Talkshow': 'Talk Show',
            'Amusement': 'Entertainment',
            'Entertainment': 'Entertainment',
            'Quiz': 'Game Show',
            'Reality': 'Reality',
            'Soap': 'Soap Opera',
            'Serie': 'Series',
            'Film': 'Movie',
            
            # French genre mappings (common ones)
            'Action': 'Action',
            'Aventure': 'Adventure',
            'Comédie': 'Comedy',
            'Drame': 'Drama',
            'Thriller': 'Thriller',
            'Horreur': 'Horror',
            'Science-fiction': 'Science Fiction',
            'Fantastique': 'Fantasy',
            'Romance': 'Romance',
            'Western': 'Western',
            'Guerre': 'War',
            'Historique': 'Historical',
            'Policier': 'Crime',
            'Documentaire': 'Documentary',
            'Actualités': 'News',
            'Informations': 'News',
            'Sport': 'Sports',
            'Football': 'Sports',
            'Automobile': 'Motorsport',
            'Musique': 'Music',
            'Jeunesse': 'Children',
            'Animation': 'Animation',
            'Éducatif': 'Educational',
            'Science': 'Science',
            'Nature': 'Nature',
            'Voyage': 'Travel',
            'Cuisine': 'Food',
            'Lifestyle': 'Lifestyle',
            'Magazine': 'Magazine',
            'Talk-show': 'Talk Show',
            'Divertissement': 'Entertainment',
            'Jeu': 'Game Show',
            'Téléréalité': 'Reality',
            'Feuilleton': 'Soap Opera',
            'Série': 'Series',
            'Film': 'Movie',
            
            # Portuguese genre mappings (common ones)
            'Ação': 'Action',
            'Aventura': 'Adventure',
            'Comédia': 'Comedy',
            'Drama': 'Drama',
            'Thriller': 'Thriller',
            'Terror': 'Horror',
            'Ficção Científica': 'Science Fiction',
            'Fantasia': 'Fantasy',
            'Romance': 'Romance',
            'Western': 'Western',
            'Guerra': 'War',
            'Histórico': 'Historical',
            'Policial': 'Crime',
            'Documentário': 'Documentary',
            'Notícias': 'News',
            'Atualidades': 'News',
            'Desporto': 'Sports',
            'Futebol': 'Sports',
            'Automobilismo': 'Motorsport',
            'Música': 'Music',
            'Infantil': 'Children',
            'Animação': 'Animation',
            'Educativo': 'Educational',
            'Ciência': 'Science',
            'Natureza': 'Nature',
            'Viagem': 'Travel',
            'Culinária': 'Food',
            'Lifestyle': 'Lifestyle',
            'Magazine': 'Magazine',
            'Talk Show': 'Talk Show',
            'Entretenimento': 'Entertainment',
            'Quiz': 'Game Show',
            'Reality Show': 'Reality',
            'Telenovela': 'Soap Opera',
            'Série': 'Series',
            'Filme': 'Movie',
            
            # Polish genre mappings (common ones)
            'Akcja': 'Action',
            'Przygodowy': 'Adventure',
            'Komedia': 'Comedy',
            'Dramat': 'Drama',
            'Thriller': 'Thriller',
            'Horror': 'Horror',
            'Science Fiction': 'Science Fiction',
            'Fantasy': 'Fantasy',
            'Romans': 'Romance',
            'Western': 'Western',
            'Wojenny': 'War',
            'Historyczny': 'Historical',
            'Kryminalny': 'Crime',
            'Dokumentalny': 'Documentary',
            'Wiadomości': 'News',
            'Aktualności': 'News',
            'Sport': 'Sports',
            'Piłka nożna': 'Sports',
            'Motorsport': 'Motorsport',
            'Muzyka': 'Music',
            'Dla dzieci': 'Children',
            'Animacja': 'Animation',
            'Edukacyjny': 'Educational',
            'Nauka': 'Science',
            'Przyroda': 'Nature',
            'Podróże': 'Travel',
            'Kuchnia': 'Food',
            'Lifestyle': 'Lifestyle',
            'Magazyn': 'Magazine',
            'Talk-show': 'Talk Show',
            'Rozrywka': 'Entertainment',
            'Quiz': 'Game Show',
            'Reality show': 'Reality',
            'Opera mydlana': 'Soap Opera',
            'Serial': 'Series',
            'Film': 'Movie'
        }
        
    def download_epg_sources(self, xml_dir: Path, force_download: bool = False) -> None:
        """Download EPG files from configured URLs with auto-compression detection."""
        if not self.sources_config:
            print("No source configurations found, skipping downloads")
            return
            
        print(f"Downloading {len(self.sources_config)} EPG sources (force_download={force_download})...")
        
        # Ensure xml directory exists
        xml_dir.mkdir(exist_ok=True)
        
        for filename, url in self.sources_config.items():
            if not url:
                print(f"Warning: No URL configured for {filename}, skipping")
                continue
                
            output_path = xml_dir / filename
            
            # Check if file exists and skip if not forcing download
            if output_path.exists() and not force_download:
                print(f"  {filename} already exists, skipping (use --force-download to override)")
                continue
                
            # Auto-detect compression from URL extension
            is_compressed = url.lower().endswith(('.gz', '.xml.gz'))
                
            try:
                print(f"  Downloading {filename} from {url}")
                
                # Create a request with proper user-agent header
                request = urllib.request.Request(url)
                request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
                
                # Download file
                if is_compressed:
                    # Download compressed file to temporary location
                    temp_path = xml_dir / f"{filename}.tmp.gz"
                    with urllib.request.urlopen(request) as response:
                        with open(temp_path, 'wb') as f:
                            shutil.copyfileobj(response, f)
                    
                    # Decompress file
                    with gzip.open(temp_path, 'rb') as f_in:
                        with open(output_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove temporary compressed file
                    temp_path.unlink()
                    print(f"    Downloaded and decompressed {filename}")
                else:
                    # Download directly
                    with urllib.request.urlopen(request) as response:
                        with open(output_path, 'wb') as f:
                            shutil.copyfileobj(response, f)
                    print(f"    Downloaded {filename}")
                    
            except urllib.error.URLError as e:
                print(f"    Error downloading {filename}: {e}")
                continue
            except Exception as e:
                print(f"    Error processing {filename}: {e}")
                continue
        
        print("Download completed")
    
    def load_channel_filter(self, filter_file: Path) -> None:
        """Load channel filter from JSON or text file."""
        try:
            with open(filter_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
                # Try to parse as JSON first
                try:
                    data = json.loads(content)
                    
                    # Load sources configuration if present
                    if isinstance(data, dict) and 'sources' in data:
                        sources_data = data['sources']
                        self.sources_config = {}
                        
                        # Handle both old and new formats
                        for filename, config in sources_data.items():
                            if isinstance(config, str):
                                # New simple format: "filename": "url"
                                self.sources_config[filename] = config
                            elif isinstance(config, dict) and 'url' in config:
                                # Old format: "filename": {"url": "...", "compressed": bool}
                                # Extract just the URL (compression is auto-detected)
                                self.sources_config[filename] = config['url']
                            else:
                                print(f"Warning: Invalid source configuration for {filename}, skipping")
                        
                        print(f"Loaded {len(self.sources_config)} source configurations")
                    
                    if isinstance(data, list):
                        # Simple list format
                        self.channel_filter = set(data)
                        self.use_advanced_config = False
                    elif isinstance(data, dict) and 'channels' in data:
                        if isinstance(data['channels'], list):
                            # Simple format: {"channels": ["id1", "id2"]}
                            self.channel_filter = set(data['channels'])
                            self.use_advanced_config = False
                        elif isinstance(data['channels'], dict):
                            # Advanced format: {"channels": {"id1": {...}, "id2": {...}}}
                            self._load_advanced_config(data['channels'])
                            self.use_advanced_config = True
                        else:
                            raise ValueError("Invalid channels format")
                    elif isinstance(data, dict):
                        # If it's a dict but no 'channels' key, try to use values if they're strings
                        values = list(data.values())
                        if values and all(isinstance(v, str) for v in values):
                            self.channel_filter = set(values)
                            self.use_advanced_config = False
                        else:
                            raise ValueError("JSON must be a list of channel IDs or object with 'channels' key")
                    else:
                        raise ValueError("JSON must be a list of channel IDs or object with 'channels' key")
                except json.JSONDecodeError:
                    # If not JSON, treat as plain text with one channel ID per line
                    self.channel_filter = set(line.strip() for line in content.split('\n') if line.strip())
                    self.use_advanced_config = False
                    
        except FileNotFoundError:
            print(f"Error: Channel filter file '{filter_file}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading channel filter file: {e}")
            sys.exit(1)
            
        if self.use_advanced_config:
            print(f"Loaded {len(self.channel_config)} channel configurations")
        else:
            print(f"Loaded {len(self.channel_filter)} channel filters")
    
    def _load_advanced_config(self, channels_config: Dict) -> None:
        """Load advanced channel configuration."""
        self.channel_config = {}
        self.channel_filter = set()
        self.requested_channels = {}  # Reset tracking
        
        for channel_id, config in channels_config.items():
            if isinstance(config, str):
                # Simple string means use default settings but only from specified source
                source_file = config
                self.channel_config[channel_id] = {'source_file': source_file}
            elif isinstance(config, dict):
                # Full configuration object
                source_file = config.get('source_file')
                self.channel_config[channel_id] = config
            else:
                print(f"Warning: Invalid configuration for channel '{channel_id}', skipping")
                continue
            
            # Track requested channels by source file
            if source_file:
                if source_file not in self.requested_channels:
                    self.requested_channels[source_file] = set()
                self.requested_channels[source_file].add(channel_id)
                
            self.channel_filter.add(channel_id)
    
    def parse_xmltv_file(self, xml_file: Path) -> None:
        """Parse a single XMLTV file and extract channels and programmes."""
        print(f"Processing {xml_file.name}...")
        
        try:
            # Parse XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            channels_found = 0
            programmes_found = 0
            
            # Initialize tracking for this file
            if xml_file.name not in self.found_channels:
                self.found_channels[xml_file.name] = set()
            
            # Extract channels
            for channel in root.findall('channel'):
                channel_id = channel.get('id')
                if channel_id:
                    # Track all channels found in this file
                    self.found_channels[xml_file.name].add(channel_id)
                    
                    if self._should_include_channel(channel_id, xml_file.name):
                        # Check if we should use this channel from this specific file
                        if self.use_advanced_config:
                            config = self.channel_config.get(channel_id, {})
                            source_file = config.get('source_file')
                            if source_file and source_file != xml_file.name and source_file != xml_file.stem + '.xml':
                                continue  # Skip this channel
                        
                        # Apply custom channel ID if configured
                        if self.use_advanced_config and channel_id in self.channel_config:
                            channel, new_channel_id = self._customize_channel(channel, channel_id)
                            self.channel_id_mapping[channel_id] = new_channel_id
                            self.channels[new_channel_id] = channel
                        else:
                            # Remove display-name elements even in simple mode
                            channel = self._remove_display_names(channel)
                            self.channels[channel_id] = channel
                        channels_found += 1
            
            # Extract programmes for filtered channels
            for programme in root.findall('programme'):
                original_channel_id = programme.get('channel')
                if original_channel_id and self._should_include_channel(original_channel_id, xml_file.name):
                    # Check if we should use programmes from this specific file for this channel
                    if self.use_advanced_config:
                        config = self.channel_config.get(original_channel_id, {})
                        source_file = config.get('source_file')
                        if source_file and source_file != xml_file.name and source_file != xml_file.stem + '.xml':
                            continue  # Skip programmes from this file for this channel
                    
                    # Update channel reference in programme if we have a mapping
                    new_channel_id = self.channel_id_mapping.get(original_channel_id, original_channel_id)
                    programme.set('channel', new_channel_id)
                    
                    # Remove poster images (icon tags) from programme for better PVR compatibility
                    programme = self._remove_programme_icons(programme)
                    
                    # Standardize and enhance programme formatting
                    programme = self._standardize_programme(programme)
                    
                    self.programmes.append(programme)
                    programmes_found += 1
            
            print(f"  Found {channels_found} channels and {programmes_found} programmes")
            
        except ET.ParseError as e:
            print(f"Error parsing {xml_file}: {e}")
        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
    
    def _should_include_channel(self, channel_id: str, filename: str) -> bool:
        """Check if a channel should be included based on filter settings."""
        if not self.channel_filter:
            return True  # No filter, include all
        return channel_id in self.channel_filter
    
    def _customize_channel(self, channel: ET.Element, original_channel_id: str) -> tuple:
        """Apply custom channel ID and remove display names. Returns (new_channel, new_channel_id)."""
        config = self.channel_config.get(original_channel_id, {})
        
        # Get the custom channel ID, or use the original if not specified
        new_channel_id = config.get('output_id', original_channel_id)
        
        # Create a new channel element to avoid modifying the original
        new_channel = ET.Element('channel')
        new_channel.set('id', new_channel_id)
        
        # Copy existing attributes except id
        for key, value in channel.attrib.items():
            if key != 'id':
                new_channel.set(key, value)
        
        # Only copy icon and other elements, skip display-name elements
        custom_icon = config.get('icon')
        if custom_icon:
            icon = ET.SubElement(new_channel, 'icon')
            icon.set('src', custom_icon)
        else:
            for icon in channel.findall('icon'):
                new_icon = ET.SubElement(new_channel, 'icon')
                for key, value in icon.attrib.items():
                    new_icon.set(key, value)
        
        # Copy other elements except display-name
        for element in channel:
            if element.tag not in ['display-name', 'icon']:
                new_channel.append(element)
        
        return new_channel, new_channel_id
    
    def _remove_display_names(self, channel: ET.Element) -> ET.Element:
        """Remove display-name elements from a channel while keeping other elements."""
        # Create a new channel element
        new_channel = ET.Element('channel')
        
        # Copy all attributes
        for key, value in channel.attrib.items():
            new_channel.set(key, value)
        
        # Copy all elements except display-name
        for element in channel:
            if element.tag != 'display-name':
                new_channel.append(element)
        
        return new_channel
    
    def _remove_programme_icons(self, programme: ET.Element) -> ET.Element:
        """Remove icon elements from a programme for better PVR compatibility."""
        # Create a new programme element
        new_programme = ET.Element('programme')
        
        # Copy all attributes
        for key, value in programme.attrib.items():
            new_programme.set(key, value)
        
        # Copy all elements except icon tags
        for element in programme:
            if element.tag != 'icon':
                new_programme.append(element)
        
        return new_programme
    
    def _standardize_programme(self, programme: ET.Element) -> ET.Element:
        """Standardize programme formatting across different sources."""
        # Create a new programme element with standardized structure
        new_programme = ET.Element('programme')
        
        # Copy all attributes (start, stop, channel)
        for key, value in programme.attrib.items():
            new_programme.set(key, value)
        
        # Get existing elements
        title_elem = programme.find('title')
        desc_elem = programme.find('desc')
        subtitle_elem = programme.find('sub-title')
        category_elems = programme.findall('category')
        episode_num_elem = programme.find('episode-num')
        rating_elem = programme.find('rating')
        
        # Process title (always required)
        if title_elem is not None:
            new_title = ET.SubElement(new_programme, 'title')
            new_title.text = self._clean_title(title_elem.text or '')
            if title_elem.get('lang'):
                new_title.set('lang', title_elem.get('lang'))
        
        # Process subtitle if exists
        if subtitle_elem is not None and subtitle_elem.text:
            new_subtitle = ET.SubElement(new_programme, 'sub-title')
            new_subtitle.text = subtitle_elem.text.strip()
            if subtitle_elem.get('lang'):
                new_subtitle.set('lang', subtitle_elem.get('lang'))
        
        # Process and enhance description
        if desc_elem is not None and desc_elem.text:
            desc_text = desc_elem.text.strip()
            enhanced_desc, extracted_info = self._extract_info_from_description(desc_text)
            
            # Add cleaned description (only if not empty)
            if enhanced_desc:
                new_desc = ET.SubElement(new_programme, 'desc')
                new_desc.text = enhanced_desc
                if desc_elem.get('lang'):
                    new_desc.set('lang', desc_elem.get('lang'))
            
            # Add extracted categories if none exist
            if not category_elems and extracted_info.get('genre'):
                # Map Spanish genre to English for TVHeadend compatibility
                mapped_genre = self._map_genre_to_english(extracted_info['genre'])
                new_category = ET.SubElement(new_programme, 'category')
                new_category.text = mapped_genre
                # Use English language for mapped genres
                new_category.set('lang', 'en')
            
            # Add date if extracted and no episode info exists
            if extracted_info.get('year') and not episode_num_elem:
                new_date = ET.SubElement(new_programme, 'date')
                new_date.text = extracted_info['year']
            
            # Add credits if extracted
            if extracted_info.get('credits'):
                credits_elem = ET.SubElement(new_programme, 'credits')
                for role, names in extracted_info['credits'].items():
                    for name in names:
                        credit_elem = ET.SubElement(credits_elem, role)
                        credit_elem.text = name
            
            # Add rating if extracted and none exists
            if extracted_info.get('rating') and not rating_elem:
                new_rating = ET.SubElement(new_programme, 'rating')
                value_elem = ET.SubElement(new_rating, 'value')
                value_elem.text = extracted_info['rating']
        
        # Copy existing categories with genre mapping
        for category in category_elems:
            if category.text and category.text.strip():
                # Map Spanish genre to English for TVHeadend compatibility
                mapped_genre = self._map_genre_to_english(category.text.strip())
                new_category = ET.SubElement(new_programme, 'category')
                new_category.text = mapped_genre
                # Use English language for mapped genres
                new_category.set('lang', 'en')
        
        # Copy episode information
        if episode_num_elem is not None and episode_num_elem.text:
            new_episode = ET.SubElement(new_programme, 'episode-num')
            new_episode.text = episode_num_elem.text
            if episode_num_elem.get('system'):
                new_episode.set('system', episode_num_elem.get('system'))
        
        # Copy rating information
        if rating_elem is not None:
            new_rating = ET.SubElement(new_programme, 'rating')
            if rating_elem.get('system'):
                new_rating.set('system', rating_elem.get('system'))
            for child in rating_elem:
                new_rating.append(child)
        
        # Copy any other elements that we haven't processed (but skip icons)
        for element in programme:
            if element.tag not in ['title', 'sub-title', 'desc', 'category', 'episode-num', 'rating', 'icon', 'credits', 'date']:
                new_programme.append(element)
        
        return new_programme
    
    def _clean_title(self, title: str) -> str:
        """Clean and standardize programme titles."""
        if not title:
            return ''
        
        # Remove excessive information from title
        title = title.strip()
        
        # Remove season/episode info that should be in episode-num instead
        import re
        title = re.sub(r'\s*-\s*Stag\.\s*\d+\s*Ep\.\s*\d+\s*$', '', title)
        title = re.sub(r'\s*T\d+\s*E\d+\s*$', '', title)
        
        return title.strip()
    
    def _extract_info_from_description(self, desc: str) -> tuple:
        """Extract structured information from description text."""
        import re
        
        extracted_info = {
            'genre': None,
            'year': None,
            'rating': None,
            'credits': {}
        }
        
        lines = desc.split('\n')
        main_desc = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip technical metadata lines (but extract useful info)
            # Only skip if line starts with "·" and then immediately has a metadata keyword
            # OR if line starts directly with a metadata keyword (no "·")
            if not line.startswith('·') and any(keyword in line.lower() for keyword in [
                'país:', 'country:', 'título original:', 'original title:',
                'dirección:', 'direction:', 'reparto:', 'cast:', 
                'guion:', 'script:', 'música:', 'music:',
                'producción:', 'production:', 'productora:', 'producer:',
                'presenta:', 'presents:'
            ]):
                # Extract credits information
                if 'dirección:' in line.lower() or 'direction:' in line.lower():
                    directors = re.findall(r'(?:dirección:|direction:)\s*([^.]*(?:\.[^A-Z][^.]*)*)', line, re.IGNORECASE)
                    if directors:
                        extracted_info['credits']['director'] = [d.strip() for d in directors[0].split(',')]
                
                if 'presenta:' in line.lower():
                    presenters = re.findall(r'presenta:\s*([^.]*(?:\.[^A-Z][^.]*)*)', line, re.IGNORECASE)
                    if presenters:
                        extracted_info['credits']['presenter'] = [p.strip() for p in presenters[0].split(',')]
                
                if 'reparto:' in line.lower():
                    actors = re.findall(r'reparto:\s*([^.]*(?:\.[^A-Z][^.]*)*)', line, re.IGNORECASE)
                    if actors:
                        extracted_info['credits']['actor'] = [a.strip() for a in actors[0].split(',')]
                
                if 'producción:' in line.lower():
                    producers = re.findall(r'producción:\s*([^.]*(?:\.[^A-Z][^.]*)*)', line, re.IGNORECASE)
                    if producers:
                        extracted_info['credits']['producer'] = [p.strip() for p in producers[0].split(',')]
                
                continue  # Skip this line from description
            
            # Also handle lines that start with "·" but are primarily metadata
            elif line.startswith('·') and any(line.lower().strip()[1:].strip().startswith(keyword) for keyword in [
                'país:', 'country:', 'título original:', 'original title:',
                'dirección:', 'direction:', 'reparto:', 'cast:', 
                'guion:', 'script:', 'música:', 'music:',
                'producción:', 'production:', 'productora:', 'producer:',
                'presenta:', 'presents:'
            ]):
                # Extract credits information from "·" lines
                content = line[1:].strip()  # Remove "·" marker
                if 'dirección:' in content.lower() or 'direction:' in content.lower():
                    directors = re.findall(r'(?:dirección:|direction:)\s*([^.]*(?:\.[^A-Z][^.]*)*)', content, re.IGNORECASE)
                    if directors:
                        extracted_info['credits']['director'] = [d.strip() for d in directors[0].split(',')]
                
                if 'presenta:' in content.lower():
                    presenters = re.findall(r'presenta:\s*([^.]*(?:\.[^A-Z][^.]*)*)', content, re.IGNORECASE)
                    if presenters:
                        extracted_info['credits']['presenter'] = [p.strip() for p in presenters[0].split(',')]
                
                if 'reparto:' in content.lower():
                    actors = re.findall(r'reparto:\s*([^.]*(?:\.[^A-Z][^.]*)*)', content, re.IGNORECASE)
                    if actors:
                        extracted_info['credits']['actor'] = [a.strip() for a in actors[0].split(',')]
                
                if 'producción:' in content.lower():
                    producers = re.findall(r'producción:\s*([^.]*(?:\.[^A-Z][^.]*)*)', content, re.IGNORECASE)
                    if producers:
                        extracted_info['credits']['producer'] = [p.strip() for p in producers[0].split(',')]
                
                continue  # Skip this line from description
            
            # Extract year and genre from first line if it contains metadata
            if '|' in line and any(char.isdigit() for char in line):
                parts = line.split('|')
                for i, part in enumerate(parts):
                    part = part.strip()
                    # Look for year (4 digits)
                    year_match = re.search(r'\b(19|20)\d{2}\b', part)
                    if year_match and not extracted_info['year']:
                        extracted_info['year'] = year_match.group()
                    
                    # Look for rating
                    if '+' in part and any(char.isdigit() for char in part):
                        extracted_info['rating'] = part
                    
                    # First part is usually genre (if no digits and no rating)
                    if i == 0 and not extracted_info['genre'] and not any(char.isdigit() for char in part) and '+' not in part:
                        extracted_info['genre'] = part
                continue  # Skip this metadata line from description
            
            # This is content for the main description
            # Only include lines that start with "·" and contain actual description content
            if line.startswith('·'):
                desc_content = line[1:].strip()  # Remove the "·" marker
                
                # Handle mixed content lines that contain both description and metadata
                # Split at first occurrence of technical metadata keywords
                metadata_keywords = [
                    'realizacion:', 'produccion:', 'productora:', 'productor ejecutivo:',
                    'guion:', 'música:', 'reparto:', 'dirección:'
                ]
                
                # Find the first occurrence of any metadata keyword
                split_point = len(desc_content)
                for keyword in metadata_keywords:
                    pos = desc_content.lower().find(keyword)
                    if pos != -1 and pos < split_point:
                        split_point = pos
                
                # Extract the description part (before metadata)
                if split_point < len(desc_content):
                    desc_content = desc_content[:split_point].strip()
                    # Remove trailing punctuation if it was cut off
                    desc_content = re.sub(r'[;.,]+$', '', desc_content).strip()
                
                # Check if this starts with technical keywords first
                if any(desc_content.lower().startswith(keyword) for keyword in [
                    'título original:', 'país:', 'dirección:', 'reparto:', 
                    'guion:', 'música:', 'producción:', 'productora:',
                    'realizacion:', 'productor ejecutivo:'
                ]):
                    continue  # Skip technical metadata lines
                
                # Check if this is actual description content (length check)
                if len(desc_content) > 15:
                    # Clean up "Votos:" at the end if present
                    desc_content = re.sub(r'\s*votos:\s*\d+.*$', '', desc_content, flags=re.IGNORECASE)
                    desc_content = desc_content.strip()
                    if desc_content:  # Only add non-empty content
                        main_desc.append(desc_content)
        
        # Clean up the main description
        clean_desc = ' '.join(main_desc).strip()
        
        # Remove redundant information and clean up
        clean_desc = re.sub(r'\s*votos:\s*\d+.*$', '', clean_desc, flags=re.IGNORECASE)
        
        return clean_desc, extracted_info
    
    def merge_files(self, xml_files: List[Path]) -> None:
        """Merge multiple XMLTV files."""
        print(f"Merging {len(xml_files)} XMLTV files...")
        
        for xml_file in xml_files:
            if xml_file.exists() and xml_file.suffix.lower() == '.xml':
                self.parse_xmltv_file(xml_file)
            else:
                print(f"Warning: Skipping {xml_file} (not found or not an XML file)")
        
        # Validate requested channels after processing all files
        self._validate_requested_channels()
    
    def generate_output(self, output_file: Path) -> None:
        """Generate the merged XMLTV output file."""
        print(f"Generating output file: {output_file}")
        
        # Create root element
        root = ET.Element('tv')
        
        # Add generator info
        generator_name = f"XMLTV Merger - Generated on {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        root.set('generator-info-name', generator_name)
        root.set('generator-info-url', 'https://github.com/alvarocandela/epg-grab')
        
        # Add channels (sorted by ID for consistency)
        for channel_id in sorted(self.channels.keys()):
            root.append(self.channels[channel_id])
        
        # Add programmes (sorted by start time and channel)
        self.programmes.sort(key=lambda p: (p.get('start', ''), p.get('channel', '')))
        for programme in self.programmes:
            root.append(programme)
        
        # Create tree and write to file
        tree = ET.ElementTree(root)
        
        # Pretty print the XML
        self._indent(root)
        
        # Write with XML declaration
        try:
            with open(output_file, 'wb') as f:
                tree.write(f, encoding='utf-8', xml_declaration=True)
            
            print(f"Successfully created {output_file}")
            print(f"  Total channels: {len(self.channels)}")
            print(f"  Total programmes: {len(self.programmes)}")
            
        except Exception as e:
            print(f"Error writing output file: {e}")
            sys.exit(1)
    
    def _indent(self, elem, level=0):
        """Add pretty-printing indentation to XML elements."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self._indent(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def show_available_channels(self, xml_files: List[Path]) -> None:
        """Show all available channels across all input files."""
        print("Scanning for available channels...")
        
        all_channels = {}
        
        for xml_file in xml_files:
            if not xml_file.exists() or xml_file.suffix.lower() != '.xml':
                continue
                
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                for channel in root.findall('channel'):
                    channel_id = channel.get('id')
                    if channel_id:
                        display_names = [dn.text for dn in channel.findall('display-name') if dn.text]
                        all_channels[channel_id] = {
                            'display_names': display_names,
                            'source_file': xml_file.name
                        }
                        
            except Exception as e:
                print(f"Error reading {xml_file}: {e}")
        
        # Display results
        print(f"\nFound {len(all_channels)} unique channels:")
        print("-" * 80)
        
        for channel_id in sorted(all_channels.keys()):
            info = all_channels[channel_id]
            display_name = info['display_names'][0] if info['display_names'] else 'No display name'
            print(f"ID: {channel_id}")
            print(f"    Display Name: {display_name}")
            print(f"    Source: {info['source_file']}")
            if len(info['display_names']) > 1:
                print(f"    Other names: {', '.join(info['display_names'][1:])}")
            print()

    def _validate_requested_channels(self) -> None:
        """Validate that all requested channels were found in their source files."""
        if not self.use_advanced_config or not self.requested_channels:
            return
        
        errors_found = False
        
        for source_file, requested_channels in self.requested_channels.items():
            found_channels = self.found_channels.get(source_file, set())
            missing_channels = requested_channels - found_channels
            
            if missing_channels:
                if not errors_found:
                    print("\n" + "="*60)
                    print("CHANNEL VALIDATION ERRORS")
                    print("="*60)
                    errors_found = True
                
                print(f"\nSource file: {source_file}")
                print(f"Missing channels ({len(missing_channels)}):")
                for channel in sorted(missing_channels):
                    output_id = self.channel_config.get(channel, {}).get('output_id', channel)
                    print(f"  ERROR: '{channel}' not found in {source_file}")
                    if output_id != channel:
                        print(f"         (configured output_id: '{output_id}')")
        
        if errors_found:
            print("\n" + "="*60)
            print("Use --list-channels to see all available channels")
            print("="*60 + "\n")
    
    def _map_genre_to_english(self, spanish_genre: str) -> str:
        """Map Spanish genre to English equivalent for TVHeadend compatibility."""
        if not spanish_genre:
            return spanish_genre
            
        # Clean the genre string
        genre = spanish_genre.strip()
        
        # Try exact match first
        if genre in self.genre_mapping:
            return self.genre_mapping[genre]
        
        # Try partial matches for slash-separated genres (e.g., "Información/Reportaje")
        # Check if it's a compound genre with slash
        if '/' in genre:
            # Try the full compound genre first
            if genre in self.genre_mapping:
                return self.genre_mapping[genre]
            
            # Try just the second part (more specific genre)
            parts = genre.split('/')
            if len(parts) >= 2:
                second_part = parts[1].strip()
                if second_part in self.genre_mapping:
                    return self.genre_mapping[second_part]
                
                # Try the first part as fallback
                first_part = parts[0].strip()
                if first_part in self.genre_mapping:
                    return self.genre_mapping[first_part]
        
        # Try case-insensitive match
        for spanish, english in self.genre_mapping.items():
            if genre.lower() == spanish.lower():
                return english
        
        # If no mapping found, return original but cleaned
        return genre
def main():
    parser = argparse.ArgumentParser(
        description="Merge XMLTV files and filter channels with automatic EPG download support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download fresh EPG data and merge (ideal for cron jobs)
  python xmltv_merger.py
  
  # Download only (skip merging)
  python xmltv_merger.py --download-only
  
  # Use existing files without downloading
  python xmltv_merger.py --skip-download
  
  # Merge specific files with filtering
  python xmltv_merger.py -i xml/australia.xml xml/nz.xml -f channels.json -o merged.xml
  
  # Show all available channels
  python xmltv_merger.py -i xml/*.xml --list-channels
  
  # Merge without filtering (include all channels)
  python xmltv_merger.py -i xml/*.xml -o merged.xml
        """
    )
    
    parser.add_argument('-i', '--input', nargs='+', default=['xml/*.xml'],
                       help='Input XMLTV files (supports wildcards, default: xml/*.xml)')
    parser.add_argument('-f', '--filter', type=Path, default=Path('channels.json'),
                       help='Channel filter file (JSON or text format, default: channels.json)')
    parser.add_argument('-o', '--output', type=Path, default=Path('combined.xml'),
                       help='Output XMLTV file (default: combined.xml)')
    parser.add_argument('--list-channels', action='store_true',
                       help='List all available channels and exit')
    parser.add_argument('--force-download', action='store_true',
                       help='Force download of EPG sources even if files exist (default for cron jobs)')
    parser.add_argument('--download-only', action='store_true',
                       help='Download EPG sources only, skip merging')
    parser.add_argument('--skip-download', action='store_true',
                       help='Skip automatic EPG download, use existing files only')
    
    args = parser.parse_args()
    
    merger = XMLTVMerger()
    
    # Load channel filter if provided to get source configurations
    if args.filter:
        merger.load_channel_filter(args.filter)
    
    # Download EPG sources if configured and not skipped
    if not args.skip_download and merger.sources_config:
        xml_dir = Path('xml')
        # For cron jobs: force download by default unless specifically disabled
        # Only skip force when --skip-download is used or files don't exist yet
        force_download = args.force_download or not args.skip_download
        merger.download_epg_sources(xml_dir, force_download=force_download)
    
    # If download-only flag is set, exit after downloading
    if args.download_only:
        print("Download completed. Exiting without merging.")
        return
    
    # Convert input paths to Path objects
    input_files = []
    for pattern in args.input:
        if '*' in pattern or '?' in pattern:
            # Handle wildcards
            import glob
            input_files.extend([Path(f) for f in glob.glob(pattern)])
        else:
            input_files.append(Path(pattern))
    
    if not input_files:
        print("Error: No input files found")
        sys.exit(1)
    
    # If list-channels flag is set, show available channels and exit
    if args.list_channels:
        merger.show_available_channels(input_files)
        return
    # Merge files
    merger.merge_files(input_files)
    
    # Generate output
    if args.output:
        merger.generate_output(args.output)
    else:
        print("No output file specified. Use -o/--output to save the merged file.")


if __name__ == '__main__':
    main()
