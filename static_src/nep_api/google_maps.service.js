// Most of this code is directly from https://developers.google.com/maps/documentation/javascript/examples/places-searchbox

/* global google */

(function() {

  'use strict';

  angular
    .module('nepApi')
    .service('googleMaps', [
      '$q', '$timeout', '$rootScope', '$window',
      function googleMaps($q, $timeout, $rootScope, $window) {

        var markers = [];

        var createMap = function (mapId, inputId, placeCallback, onMapLoad) {
          // Takes the DOM id of the element to attach the map to, and the input
          // to turn into the map search box. The callback will be called on the
          // maps event 'place_changed', given the place selected by the user.
          //
          // Adds smart geolocation and default locations to _createMap().
          //
          // Returns a promise, which resolves with the map object.

          // The PERTS office
          var defaultLatLng = {
            lat: 37.7820826,
            lng: -122.4064867
          };

          var map;

          $q(function (resolve, reject) {
            if ("geolocation" in $window.navigator) {
              $window.navigator.geolocation.getCurrentPosition(
                function success(position) {
                  // Geolocation available and allowed. Use to center the map.
                  var latLng = {lat: position.coords.latitude,
                    lng: position.coords.longitude};
                    map = _createMap(mapId, inputId, placeCallback, latLng);
                    resolve(map);
                },
                function error() {
                  // Geolocation available but doesn't work, likely blocked by user.
                  // Use default location.
                  map = _createMap(mapId, inputId, placeCallback, defaultLatLng);
                  resolve(map);
                }
              );
            } else {
              // Geolocation not supported by browser. Use default location.
              map = _createMap(mapId, inputId, placeCallback, defaultLatLng);
              resolve(map);
            }
          })
          .then(function (map) {
            // Borrow the bounds changed event as a loading event. Ensures that the
            // map is ready when the event fires.
            var handle = map.addListener('bounds_changed', function() {
              // This function was fired from an event outside of Angular, so force
              // a digest loop so any modifications to scope that happen in the
              // callback are reflected in the view.
              // http://stackoverflow.com/questions/12729122/angularjs-prevent-error-digest-already-in-progress-when-calling-scope-apply#answer-18996042
              $timeout(function () {
                onMapLoad(map);
              });
              // Loading handler should only fire once.
              google.maps.event.removeListener(handle);
            });
            google.maps.event.trigger(map, 'bounds_changed');
          });
        };

        var _createMap = function (mapId, inputId, placeCallback, latLng) {
          // Build the map and the search box, which must both exist as **visible**
          // elements already.
          var mapDiv = $window.document.getElementById(mapId);
          var searchInput = $window.document.getElementById(inputId);
          var map = new google.maps.Map(mapDiv, {
            center: latLng,
            zoom: 13,
            mapTypeId: 'roadmap'
          });
          var searchBox = new google.maps.places.SearchBox(searchInput);
          // var topLeft = google.maps.ControlPosition.TOP_LEFT;
          // map.controls[topLeft].push(searchInput);

          // Bias the SearchBox results towards current map's viewport.
          map.addListener('bounds_changed', function() {
            searchBox.setBounds(map.getBounds());
          });

          // Listen for the event fired when the user selects a prediction and
          // retrieve more details for that place.
          searchBox.addListener('places_changed', function() {
            var places = searchBox.getPlaces();

            if (places.length === 0) {
              return;
            }

            // Clear out the old markers.
            markers.forEach(function(marker) {
              marker.setMap(null);
            });
            markers = [];

            // For each place, get the icon, name and location.
            var bounds = new google.maps.LatLngBounds();
            places.forEach(function(place) {
              if (!place.geometry) {
                console.log("Returned place contains no geometry");
                return;
              }
              var icon = {
                url: place.icon,
                size: new google.maps.Size(71, 71),
                origin: new google.maps.Point(0, 0),
                anchor: new google.maps.Point(17, 34),
                scaledSize: new google.maps.Size(25, 25)
              };

              // Create a marker for each place.
              markers.push(new google.maps.Marker({
                map: map,
                icon: icon,
                title: place.name,
                position: place.geometry.location
              }));

              if (place.geometry.viewport) {
                // Only geocodes have viewport.
                bounds.union(place.geometry.viewport);
              } else {
                bounds.extend(place.geometry.location);
              }
            });
            map.fitBounds(bounds);

            // This function was fired from an event outside of Angular, so force
            // a digest loop so any modifications to scope that happen in the
            // callback are reflected in the view.
            // http://stackoverflow.com/questions/12729122/angularjs-prevent-error-digest-already-in-progress-when-calling-scope-apply#answer-18996042
            $timeout(function () {
              // Assume we're only interested in the first place. I'm not actually
              // sure why this code allows for several.
              placeCallback(places[0]);
            });
          });

          return map;
        };

        return {
          createMap: createMap
        };
      }
    ]);

}());
