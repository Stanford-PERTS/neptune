// Map widget that searches for "places" with the Google Maps API.

// Provides a map load event with argument `map`.
// Provides a place change event with argument `place`.

// Example where parentMapFunction and parentPlaceFuntion are defined within
// the calling scope:
// <div nep-place-search
//      on-map-load="parentMapFunction(map)"
//      on-place-change="parentPlaceFunction(place)">
// Some of this code is from https://developers.google.com/maps/documentation/javascript/examples/places-searchbox

/* Google Maps Places Library is included in neptune.html */
/* global google */

import template from './index.html';

const nepPlaceSearch = ngModule => {
  ngModule.directive('nepPlaceSearch', function googleMaps(
    $q,
    $timeout,
    $rootScope,
    $window,
  ) {
    'use strict';

    const directiveScope = {
      placeChange: '&onPlaceChange',
      mapLoad: '&onMapLoad',
      mapLoading: '=?',
    };

    const mapId = 'place-map';
    const inputId = 'place-map-input';

    return {
      restrict: 'A',
      scope: directiveScope,
      template,
      link,
    };

    function link(scope, element, attrs) {
      // Takes the DOM id of the element to attach the map to, and the input
      // to turn into the map search box. The callback will be called on the
      // maps event 'place_changed', given the place selected by the user.
      //
      // Adds smart geolocation and default locations to createMap().
      //
      // Returns a promise, which resolves with the map object.

      // The PERTS office
      const defaultLatLng = {
        lat: 37.7820826,
        lng: -122.4064867,
      };

      const placeChange = scope.placeChange || function () {};
      const mapLoad = scope.mapLoad || function () {};

      // $q((resolve, reject) => {
      //   // How to use geolocation browser api retained for future reference.
      //   // if ("geolocation" in $window.navigator) {
      //   //   $window.navigator.geolocation.getCurrentPosition(
      //   //     function success(position) {
      //   //       // Geolocation available and allowed. Use to center the map.
      //   //       var latLng = {lat: position.coords.latitude,
      //   //                     lng: position.coords.longitude};
      //   //       map = createMap(mapId, inputId, latLng);
      //   //       resolve(map);
      //   //     },
      //   //     function error() {
      //   //       // Geolocation available but doesn't work, likely blocked by user.
      //   //       // Use default location.
      //   //       map = createMap(mapId, inputId, defaultLatLng);
      //   //       resolve(map);
      //   //     }
      //   //   );
      //   // }
      // });

      /**
       * Ensures the api is loaded and the `google` object exists.
       * @return {Promise}     resolves when `google` is truthy
       */
      const waitForMapsApi = () => $q(resolve => {
        const interval = setInterval(() => {
          if (window.google) {
            clearInterval(interval);
            resolve();
          }
        }, 50);
      });

      function addBoundsListener(map) {
        // Borrow the bounds changed event as a loading event. Ensures that the
        // map is ready when the event fires.
        var handle = map.addListener('bounds_changed', () => {
          // This function was fired from an event outside of Angular, so force
          // a digest loop so any modifications to scope that happen in the
          // callback are reflected in the view.
          // http://stackoverflow.com/questions/12729122/angularjs-prevent-error-digest-already-in-progress-when-calling-scope-apply#answer-18996042
          $timeout(() => {
            scope.mapLoading = false;
            mapLoad({ map });
          });
          // Loading handler should only fire once.
          google.maps.event.removeListener(handle);
        });
        google.maps.event.trigger(map, 'bounds_changed');
      };

      function createMap(mapId, inputId, latLng) {
        // Build the map and the search box, which must both exist as **visible**
        // elements already.
        const mapDiv = $window.document.getElementById(mapId);
        const searchInput = $window.document.getElementById(inputId);
        const map = new google.maps.Map(mapDiv, {
          // Mouse-wheeling or swiping down across the map normally captures
          // the mouse/touch event and zooms the map, which interrupts
          // scrolling the page. Don't do that.
          scrollwheel: false,
          center: latLng,
          zoom: 13,
          mapTypeId: 'roadmap',
        });
        const searchBox = new google.maps.places.SearchBox(searchInput);
        // var topLeft = google.maps.ControlPosition.TOP_LEFT;
        // map.controls[topLeft].push(searchInput);

        // Bias the SearchBox results towards current map's viewport.
        map.addListener('bounds_changed', () => {
          searchBox.setBounds(map.getBounds());
        });

        // Listen for the event fired when the user selects a prediction and
        // retrieve more details for that place.
        searchBox.addListener(
          'places_changed',
          () => selectFirstPlaceAsOrg(map, searchBox),
        );

        return map;
      }

      /* Depending on exactly how the place was retrieved (either via
       * autocomplete or a text search) full details may or may not be
       * available. Request these details if they're missing.
       * @param {Object} place from Google Maps, w/ or w/o address components
       * @returns {Object} promise resolving place w/ full details
       */
      function ensurePlaceDetails(map, place) {
        if (place.address_components) {
          return $q.when(place);
        }

        const service = new google.maps.places.PlacesService(map);
        // Convert google's callback-based API to a promise.
        return $q((resolve) => {
          // https://developers.google.com/maps/documentation/javascript/places#place_details
          service.getDetails(
            { placeId: place.place_id },
            (placeWithDetails, status) => {
              if (status !== 'OK') {
                throw new Error(
                  'google.maps.places.PlacesService getDetails() responded ' +
                  `with error status: ${status}`
                );
              }
              resolve(placeWithDetails);
            }
          );
        });
      }

      function selectFirstPlaceAsOrg(map, searchBox) {
        const places = searchBox.getPlaces();
        if (!places || places.length === 0) {
          return;
        }
        const [ placeNoDetails ] = places;

        // Get map bounds for the placeNoDetails so we can center the map.
        const bounds = new google.maps.LatLngBounds();
        if (placeNoDetails.geometry.viewport) {
          // Only geocodes have viewport.
          bounds.union(placeNoDetails.geometry.viewport);
        } else {
          bounds.extend(placeNoDetails.geometry.location);
        }
        map.fitBounds(bounds);

        // Call placeChange() with a keyword-like object b/c it's an & binding.
        ensurePlaceDetails(map, placeNoDetails)
          .then(place => placeChange({ place }));

        // This function was fired from an event outside of Angular, so
        // normally we need to worry about getting back into the digest loop so
        // any modifications to scope that happen in the callback are reflected
        // in the view. But relying on $q does that for us!
        // http://stackoverflow.com/questions/12729122/angularjs-prevent-error-digest-already-in-progress-when-calling-scope-apply#answer-18996042
      }

      $q.when()
        .then(waitForMapsApi)
        .then(() => createMap(mapId, inputId, defaultLatLng))
        .then(addBoundsListener);
    }
  });
};

export default nepPlaceSearch;
