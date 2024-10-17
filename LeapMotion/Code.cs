using Leap;
using UnityEngine;

public class Code : MonoBehaviour
{
    public LeapProvider leapProvider;

    private void OnEnable()
    {
        leapProvider.OnUpdateFrame += OnUpdateFrame;
    }

    private void OnDisable()
    {
        leapProvider.OnUpdateFrame -= OnUpdateFrame;
    }

    void OnUpdateFrame(Frame frame)
    {
        // Récupérer la main gauche et droite
        Hand leftHand = frame.GetHand(Chirality.Left);
        Hand rightHand = frame.GetHand(Chirality.Right);

        if (leftHand != null)
        {
            // Afficher la direction de la main gauche
            Vector3 leftHandDirection = leftHand.Direction;
            Debug.Log("Direction de la main gauche: " + leftHandDirection);

            // Récupérer et afficher la direction de l'index de la main gauche
        Finger leftIndexFinger = leftHand.fingers[1];
            if (leftIndexFinger != null)
            {
                Vector3 leftIndexDirection = leftIndexFinger.Direction;
                Debug.Log("Direction de l'index gauche: " + leftIndexDirection);
            }
        }

        if (rightHand != null)
        {
            // Afficher la direction de la main droite
            Vector3 rightHandDirection = rightHand.Direction;
            Debug.Log("Direction de la main droite: " + rightHandDirection);

            // Récupérer et afficher la direction de l'index de la main droite
            Finger rightIndexFinger = rightHand.fingers[1];
            if (rightIndexFinger != null)
            {
                Vector3 rightIndexDirection = rightIndexFinger.Direction;
                Debug.Log("Direction de l'index droit: " + rightIndexDirection);
            }
        }
    }
}































































// using Leap;
// using UnityEngine;

// public class Example : MonoBehaviour
// {
//     public LeapProvider leapProvider;

//     private void OnEnable()
//     {
//         leapProvider.OnUpdateFrame += OnUpdateFrame;
//     }
//     private void OnDisable()
//     {
//         leapProvider.OnUpdateFrame -= OnUpdateFrame;
//     }

//     void OnUpdateFrame(Frame frame)
//     {
//         //Use a helpful utility function to get the first hand that matches the Chirality
//         Hand _leftHand = frame.GetHand(Chirality.Left);

//         //When we have a valid left hand, we can begin searching for more Hand information
//         if(_leftHand != null)
//         {
//             OnUpdateHand(_leftHand)
//         }
//     }

//     void OnUpdateHand(Hand _hand)
//     {
//         // We found a left hand
//                 Debug.Log("We found a left hand");
//     }
// }